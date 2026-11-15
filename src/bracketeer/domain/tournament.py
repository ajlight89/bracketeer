"""The Tournament aggregate root: every change goes through its methods."""

from collections.abc import Sequence
from random import Random

from bracketeer.domain.errors import (
    DuplicateNameError,
    InvalidRatingError,
    InvalidResultError,
    InvalidSeedingError,
    NotInMatchError,
    PlayerCountError,
    TournamentStartedError,
    UnknownMatchError,
    UnknownPlayerError,
)
from bracketeer.domain.formats.base import RoundPlan, TournamentFormat
from bracketeer.domain.player import Player
from bracketeer.domain.rounds import Match, Round
from bracketeer.domain.standings import Standing
from bracketeer.domain.values import (
    MatchId,
    PlayerId,
    PlayerName,
    Result,
    is_non_negative_int,
)

MIN_PLAYERS = 2
MAX_PLAYERS = 64


class Tournament:
    """A tournament and everything in it (docs/design.md).

    Outside code refers to players by ID and never changes a Player
    directly, so every rule is checked here, in one place.
    """

    def __init__(self, name: str, tournament_format: TournamentFormat) -> None:
        self.name = name
        self.format = tournament_format
        self._players: dict[PlayerId, Player] = {}
        self._next_player_id: PlayerId = 1
        self._started = False
        self._rounds: list[Round] = []
        self._next_match_id: MatchId = 1

    @property
    def players(self) -> tuple[Player, ...]:
        """The registered players, in registration order."""
        return tuple(self._players.values())

    @property
    def started(self) -> bool:
        """True once start() has run; players and seeds are then fixed."""
        return self._started

    @property
    def rounds(self) -> tuple[Round, ...]:
        """The rounds so far, in order."""
        return tuple(self._rounds)

    def player(self, player_id: PlayerId) -> Player:
        """Return the player with this ID, or raise UnknownPlayerError."""
        try:
            return self._players[player_id]
        except KeyError:
            raise UnknownPlayerError(
                f"There's no player with ID {player_id}."
            ) from None

    def add_player(self, name: str, rating: int | None = None) -> PlayerId:
        """Register a player (R-PL-1 to R-PL-3) and return their new ID."""
        self._check_not_started()
        if len(self._players) >= MAX_PLAYERS:
            raise PlayerCountError(
                f"A tournament can have at most {MAX_PLAYERS} players."
            )
        player_name = self._checked_name(name)
        _check_rating(rating)
        player_id = self._next_player_id
        seed = len(self._players) + 1 if self._is_seeded() else None
        self._players[player_id] = Player(player_id, player_name, rating, seed)
        self._next_player_id += 1
        return player_id

    def edit_player(self, player_id: PlayerId, name: str, rating: int | None) -> None:
        """Change a player's name and rating, with the same checks as add_player."""
        self._check_not_started()
        player = self.player(player_id)
        player_name = self._checked_name(name, ignore=player_id)
        _check_rating(rating)
        player.name = player_name
        player.rating = rating

    def rename_player(self, player_id: PlayerId, name: str) -> None:
        """Correct a player's name, before or after the start (R-PL-4)."""
        player = self.player(player_id)
        player.name = self._checked_name(name, ignore=player_id)

    def remove_player(self, player_id: PlayerId) -> None:
        """Remove a registered player, renumbering the seeds with no gaps."""
        self._check_not_started()
        player = self.player(player_id)
        del self._players[player.id]
        if player.seed is not None:
            remaining = sorted(self._players.values(), key=lambda p: p.seed)
            self._assign_seeds([p.id for p in remaining])

    def seed_manually(self, order: Sequence[PlayerId]) -> None:
        """Seed players in the given order: the first ID gets seed 1 (R-SD-2)."""
        self._check_not_started()
        if sorted(order) != sorted(self._players):
            raise InvalidSeedingError(
                "A seeding order must list every player's ID exactly once."
            )
        self._assign_seeds(order)

    def seed_randomly(self, rng: Random) -> None:
        """Seed players in a random order; every order is equally likely (R-SD-2).

        The caller passes the random generator in, so tests can fix its seed.
        """
        self._check_not_started()
        order = list(self._players)
        rng.shuffle(order)
        self._assign_seeds(order)

    def seed_by_rating(self) -> None:
        """Seed by rating, highest first, with unrated players last (R-SD-2).

        Ties, and the unrated players, keep their registration order.
        """
        self._check_not_started()
        order = sorted(self._players.values(), key=_rating_order)
        self._assign_seeds([player.id for player in order])

    def start(self) -> None:
        """Fix the seeds and plan the first rounds (R-PL-1, R-SD-1, R-SD-3)."""
        self._check_not_started()
        if len(self._players) < MIN_PLAYERS:
            raise PlayerCountError(
                f"A tournament needs at least {MIN_PLAYERS} players to start."
            )
        if not self._is_seeded():
            raise InvalidSeedingError("Seed the players before starting.")
        by_seed = sorted(self._players.values(), key=lambda p: p.seed)
        plans = self.format.first_rounds([player.id for player in by_seed])
        for plan in plans:
            self._add_round(plan)
        self._started = True

    def match(self, match_id: MatchId) -> Match:
        """Return the match with this ID, or raise UnknownMatchError.

        Matches are created when the tournament starts, so before that every
        ID is unknown.
        """
        for round_ in self._rounds:
            for match in round_.matches:
                if match.id == match_id:
                    return match
        raise UnknownMatchError(f"There's no match with ID {match_id}.")

    def record_result(self, match_id: MatchId, result: Result) -> None:
        """Record a match's result, replacing any earlier one (US-07).

        Every check runs before the match changes, so a rejected result
        leaves the match as it was.
        """
        match = self.match(match_id)
        self._check_result_fits(match, result)
        match.result = result

    def clear_result(self, match_id: MatchId) -> None:
        """Remove a match's result, so the match is unplayed again (US-07 #7)."""
        self.match(match_id).result = None

    def standings(self) -> list[Standing]:
        """Work out the current standings from the results (US-09).

        They're calculated on every call, so they always match the results.
        The format decides the order (Strategy pattern).
        """
        return self.format.standings(self)

    def _is_seeded(self) -> bool:
        return any(player.seed is not None for player in self._players.values())

    def _assign_seeds(self, order: Sequence[PlayerId]) -> None:
        for seed, player_id in enumerate(order, start=1):
            self._players[player_id].seed = seed

    def _check_not_started(self) -> None:
        if self._started:
            raise TournamentStartedError(
                "The tournament has already started (R-PL-4, R-SD-3)."
            )

    def _check_result_fits(self, match: Match, result: Result) -> None:
        """Raise if the result breaks a rule for this match (R-RS-2, R-RS-5)."""
        if result.is_draw() and not self.format.allows_draws:
            raise InvalidResultError(
                "This format needs a winner in every match, so equal scores "
                "aren't allowed (R-RS-2)."
            )
        # Only a forfeit names a player; Result checks its own shape.
        forfeiter = result.forfeited_by
        if forfeiter is not None and not match.has_player(forfeiter):
            raise NotInMatchError(
                f"Player {forfeiter} isn't in match {match.id}; it's between "
                f"players {match.player_a} and {match.player_b}."
            )

    def _add_round(self, plan: RoundPlan) -> None:
        """Turn a plan into a numbered Round with numbered Matches."""
        matches = []
        for player_a, player_b in plan.pairings:
            matches.append(Match(self._next_match_id, player_a, player_b))
            self._next_match_id += 1
        number = len(self._rounds) + 1
        self._rounds.append(Round(number, matches, list(plan.byes)))

    def _checked_name(self, name: str, ignore: PlayerId | None = None) -> PlayerName:
        """Return the validated name, or raise if it's invalid or taken (R-PL-2)."""
        player_name = PlayerName(name)
        for other in self._players.values():
            if other.id != ignore and other.name.key() == player_name.key():
                raise DuplicateNameError(
                    f'The name "{player_name.text}" is already taken.'
                )
        return player_name


def _check_rating(rating: object) -> None:
    if rating is not None and not is_non_negative_int(rating):
        raise InvalidRatingError(
            f"A rating must be a whole number of 0 or more; got {rating!r}."
        )


def _rating_order(player: Player) -> tuple[int, int, int]:
    """Sort key: rated before unrated, higher rating first, then by ID."""
    if player.rating is None:
        return (1, 0, player.id)
    return (0, -player.rating, player.id)
