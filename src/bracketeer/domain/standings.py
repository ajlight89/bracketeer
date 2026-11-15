"""Standings: each player's record and rank, worked out from the results."""

from collections.abc import Sequence
from dataclasses import dataclass

from bracketeer.domain.player import Player
from bracketeer.domain.rounds import Match, Round
from bracketeer.domain.values import PlayerId, ResultKind


@dataclass(frozen=True)
class Standing:
    """One row of the standings table (US-09 #6).

    Standing is a value object: the standings are recalculated from the
    results whenever they're needed, never stored or changed.
    """

    player_id: PlayerId
    rank: int
    match_points: int
    wins: int
    draws: int
    losses: int
    game_differential: int

    def played(self) -> int:
        """Return the number of matches with a result; a bye isn't a match."""
        return self.wins + self.draws + self.losses


@dataclass
class _Tally:
    """One player's running totals while the results are counted."""

    match_points: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    game_differential: int = 0

    def count(self, match: Match, player_id: PlayerId) -> None:
        """Add one match that has a result (R-RS-3, R-RS-5, R-RS-6)."""
        result = match.result
        self.match_points += match.match_points_for(player_id)
        if result.is_draw():
            self.draws += 1
        elif match.winner() == player_id:
            self.wins += 1
        else:
            self.losses += 1
        # Only played matches have game scores; forfeits add nothing here.
        if result.kind is ResultKind.PLAYED:
            mine, theirs = result.score_a, result.score_b
            if player_id == match.player_b:
                mine, theirs = theirs, mine
            self.game_differential += mine - theirs


def round_robin_standings(
    players: Sequence[Player], rounds: Sequence[Round]
) -> list[Standing]:
    """Rank by match points, game differential, then seed (R-TB-2, R-TB-3).

    Every player gets a row, even before any results (R-TB-1). Byes add
    nothing, because a bye isn't a match (R-RS-4).
    """
    tallies = _tally_all(players, rounds)

    def order(player: Player) -> tuple[int, int, int | None]:
        # Negated, so higher points and differential sort first.
        tally = tallies[player.id]
        return (-tally.match_points, -tally.game_differential, player.seed)

    ordered = sorted(players, key=order)
    return [
        _row(player, rank, tallies[player.id])
        for rank, player in enumerate(ordered, start=1)
    ]


def placement_standings(
    players: Sequence[Player], rounds: Sequence[Round]
) -> list[Standing]:
    """Rank by the round in which each player was knocked out (R-SE-4, R-TB-4).

    Players still in the tournament share the best placement, so once the
    final is played the champion is 1st on their own. Players who share a
    placement are listed by seed.
    """
    tallies = _tally_all(players, rounds)
    still_in = len(rounds) + 1
    out_in_round = {player.id: still_in for player in players}
    for round_ in rounds:
        for match in round_.matches:
            winner = match.winner()
            if winner is not None:
                loser = match.player_b if winner == match.player_a else match.player_a
                out_in_round[loser] = round_.number

    def order(player: Player) -> tuple[int, int | None]:
        # Negated, so players knocked out later sort first.
        return (-out_in_round[player.id], player.seed)

    standings = []
    rank = 0
    previous = None
    for position, player in enumerate(sorted(players, key=order), start=1):
        # A shared placement uses up the places after it: 1, 2, 3, 3, 5.
        if out_in_round[player.id] != previous:
            rank = position
            previous = out_in_round[player.id]
        standings.append(_row(player, rank, tallies[player.id]))
    return standings


def _tally_all(
    players: Sequence[Player], rounds: Sequence[Round]
) -> dict[PlayerId, _Tally]:
    """Count every result into one tally per player."""
    tallies = {player.id: _Tally() for player in players}
    for round_ in rounds:
        for match in round_.matches:
            if match.result is not None:
                tallies[match.player_a].count(match, match.player_a)
                tallies[match.player_b].count(match, match.player_b)
    return tallies


def _row(player: Player, rank: int, tally: _Tally) -> Standing:
    """Build one row of the standings from a player's rank and tally."""
    return Standing(
        player.id,
        rank,
        tally.match_points,
        tally.wins,
        tally.draws,
        tally.losses,
        tally.game_differential,
    )
