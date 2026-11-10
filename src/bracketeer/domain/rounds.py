"""The Match and Round entities."""

from dataclasses import dataclass, field

from bracketeer.domain.errors import NotInMatchError
from bracketeer.domain.values import MatchId, PlayerId, Result, ResultKind

# Match points (R-RS-3).
WIN_POINTS = 3
DRAW_POINTS = 1
LOSS_POINTS = 0


@dataclass(eq=False)
class Match:
    """Two players, referred to by ID, and a result once one is recorded.

    Match is an entity: its result is entered, corrected, or cleared while it
    stays the same match, so == compares identity, not values.
    """

    id: MatchId
    player_a: PlayerId
    player_b: PlayerId
    result: Result | None = None

    def has_player(self, player_id: PlayerId) -> bool:
        """Return True if the player is one of this match's two players."""
        return player_id in (self.player_a, self.player_b)

    def winner(self) -> PlayerId | None:
        """Return the winner's ID, or None if there's no result or a draw."""
        result = self.result
        if result is None or result.is_draw():
            return None
        if result.kind is ResultKind.FORFEIT:
            return self._opponent_of(result.forfeited_by)
        if result.score_a > result.score_b:
            return self.player_a
        return self.player_b

    def match_points_for(self, player_id: PlayerId) -> int:
        """Return the match points the player earned here (R-RS-3, R-RS-5).

        A match with no result hasn't given anyone points yet.
        """
        self._check_has_player(player_id)
        if self.result is None:
            return 0
        if self.result.is_draw():
            return DRAW_POINTS
        if self.winner() == player_id:
            return WIN_POINTS
        return LOSS_POINTS

    def _check_has_player(self, player_id: PlayerId) -> None:
        if not self.has_player(player_id):
            raise NotInMatchError(
                f"Player {player_id} isn't in match {self.id}; it's between "
                f"players {self.player_a} and {self.player_b}."
            )

    def _opponent_of(self, player_id: PlayerId) -> PlayerId:
        self._check_has_player(player_id)
        if player_id == self.player_a:
            return self.player_b
        return self.player_a


@dataclass(eq=False)
class Round:
    """A numbered set of matches plus the players who have a bye.

    byes is a list because single elimination can give several byes in
    round 1 (R-SE-1); round robin gives at most one per round (R-RD-3).
    """

    number: int
    matches: list[Match]
    byes: list[PlayerId] = field(default_factory=list)

    def is_finished(self) -> bool:
        """Return True when every match has a result."""
        return all(match.result is not None for match in self.matches)
