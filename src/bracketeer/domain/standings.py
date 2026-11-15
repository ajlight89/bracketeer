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
    nothing, because a by isn't a match (R-RS-4).
    """
    tallies = {player.id: _Tally() for player in players}
    for round_ in rounds:
        for match in round_.matches:
            if match.result is not None:
                tallies[match.player_a].count(match, match.player_a)
                tallies[match.player_b].count(match, match.player_b)

    def order(player: Player) -> tuple[int, int, int | None]:
        # Negated, so higher points and differential sort first.
        tally = tallies[player.id]
        return (-tally.match_points, -tally.game_differential, player.seed)

    standings = []
    for rank, player in enumerate(sorted(players, key=order), start=1):
        tally = tallies[player.id]
        standings.append(
            Standing(
                player.id,
                rank,
                tally.match_points,
                tally.wins,
                tally.draws,
                tally.losses,
                tally.game_differential,
            )
        )
    return standings
