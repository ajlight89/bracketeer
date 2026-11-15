"""The single elimination formmat: lose once and you're out (R-SE)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from bracketeer.domain.formats.base import RoundPlan, TournamentFormat
from bracketeer.domain.standings import Standing, placement_standings
from bracketeer.domain.values import PlayerId

if TYPE_CHECKING:
    from bracketeer.domain.tournament import Tournament


class SingleElimination(TournamentFormat):
    """Single elimination with byes for the top seeds  (R-SE-1 to R-SE-4)."""

    key = "single_elimination"
    allows_draws = False  # R-RS-2
    locks_results = True  # R-RS-7

    def first_rounds(self, seeded: Sequence[PlayerId]) -> list[RoundPlan]:
        """Plan round 1 only, because later rounds depend on who wins.

        Players are placed in standard bracket order (R-SE-2), and an empty
        slot gives the player it's paired with a bye (R-SE-1).
        """
        pairs = _bracket_pairs(seeded)
        pairings = tuple((top, bottom) for top, bottom in pairs if bottom is not None)
        byes = tuple(top for top, bottom in pairs if bottom is None)
        return [RoundPlan(pairings, byes)]

    def next_round(self, tournament: Tournament) -> RoundPlan | None:
        """Pair the players who advanced from the last round (R-SE-3).

        Return None if the last round was the final. Tournament checks that
        every match in the last round has a result before calling this.
        """
        last = tournament.rounds[-1]
        if len(last.matches) == 1 and not last.byes:
            return None
        if last.number == 1:
            advancing = _round_one_advancers(tournament)
        else:
            advancing = [match.winner() for match in last.matches]
        return RoundPlan(tuple(zip(advancing[::2], advancing[1::2], strict=True)))

    def standings(self, tournament: Tournament) -> list[Standing]:
        """Rank by the round each player was knocked out in (R-TB-4)."""
        return placement_standings(tournament.players, tournament.rounds)


def _bracket_size(player_count: int) -> int:
    """Return the smallest power of 2 that is at least player_count (R-SE-1)."""
    size = 1
    while size < player_count:
        size *= 2
    return size


def _bracket_order(size: int) -> list[int]:
    """Return the seeds in standard bracket order (R-SE-2).

    Each pass doubles the bracket by following every seed with the seed it
    meets first, so the two seeds in a pair add up to the new size plus 1:
    [1] -> [1, 2] -> [1, 4, 2, 3] -> [1, 8, 4, 5, 2, 7, 3, 6].
    """
    order = [1]
    while len(order) < size:
        pair_total = 2 * len(order) + 1
        doubled = []
        for top in order:
            doubled.extend([top, pair_total - top])
        order = doubled
    return order


def _bracket_pairs(
    seeded: Sequence[PlayerId],
) -> list[tuple[PlayerId, PlayerId | None]]:
    """Pair the players in bracket order; None is an empty slot (a bye).

    The higher seed always comes first in a pair, so it becomes player A.
    """
    slots = [
        seeded[seed - 1] if seed <= len(seeded) else None
        for seed in _bracket_order(_bracket_size(len(seeded)))
    ]
    return list(zip(slots[::2], slots[1::2], strict=True))


def _round_one_advancers(tournament: Tournament) -> list[PlayerId | None]:
    """List the players who advance from round 1, in bracket order.

    Round 1 is the only round with byes, and a bye isn't a match, so the
    bracket order is rebuilt from the seeds. In every round 1 match the
    higher seed is player A, so winners are looked up by player A.
    """
    by_seed = sorted(tournament.players, key=lambda player: player.seed)
    winners = {match.player_a: match.winner() for match in tournament.rounds[0].matches}
    pairs = _bracket_pairs([player.id for player in by_seed])
    return [top if bottom is None else winners[top] for top, bottom in pairs]
