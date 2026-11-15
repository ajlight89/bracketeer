"""The round robin format: everyone plays everyone once (R-RR)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from bracketeer.domain.formats.base import RoundPlan, TournamentFormat
from bracketeer.domain.standings import Standing, round_robin_standings
from bracketeer.domain.values import PlayerId

if TYPE_CHECKING:
    from bracketeer.domain.tournament import Tournament


class RoundRobin(TournamentFormat):
    """Round robin, scheduled with the circle method (R-RR-1 to R-RR-3)."""

    key = "round_robin"
    allows_draws = True  # R-RS-2
    locks_results = False  # R-RS-7

    def first_rounds(self, seeded: Sequence[PlayerId]) -> list[RoundPlan]:
        """Plan the whole schedule at the start (R-RR-3).

        The first slot stays in place while the others move one slot each
        round. With an odd number of players, an empty slot is added, and
        whoever is paired with it has a bye (R-RR-2).
        """
        slots: list[PlayerId | None] = list(seeded)
        if len(slots) % 2 == 1:
            slots.append(None)
        plans = []
        for _ in range(len(slots) - 1):
            plans.append(_plan_round(slots))
            slots = [slots[0], slots[-1], *slots[1:-1]]
        return plans

    def next_round(self, tournament: Tournament) -> RoundPlan | None:
        """Return None: the whole schedule is planned at the start."""
        return None

    def standings(self, tournament: Tournament) -> list[Standing]:
        """Rank by match points, game differential, then seed (R-TB-2, R-TB-3)."""
        return round_robin_standings(tournament.players, tournament.rounds)


def _plan_round(slots: list[PlayerId | None]) -> RoundPlan:
    """Pair slot i with slot n - 1 - i; whoever faces the empty slot has a bye."""
    half = len(slots) // 2
    pairings = []
    byes = []
    for a, b in zip(slots[:half], reversed(slots[half:]), strict=True):
        if a is None:
            byes.append(b)
        elif b is None:
            byes.append(a)
        else:
            pairings.append((a, b))
    return RoundPlan(tuple(pairings), tuple(byes))
