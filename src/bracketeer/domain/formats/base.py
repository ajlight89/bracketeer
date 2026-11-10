"""The tournament format interface (Strategy pattern, docs/design.md)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from bracketeer.domain.values import PlayerId

if TYPE_CHECKING:
    from bracketeer.domain.tournament import Tournament


@dataclass(frozen=True)
class RoundPlan:
    """The pairings and byes for one round, before matches are numbered.

    A format returns plans; the tournament turns them into numbered Round
    and Match objects, so match IDs are handed out in one place.
    """

    pairings: tuple[tuple[PlayerId, PlayerId], ...]
    byes: tuple[PlayerId, ...] = ()


class TournamentFormat(ABC):
    """The rules that differ between tournament formats.

    Each concrete format is a strategy, and Tournament is the context that
    uses it. Formats answer questions and never change the tournament.
    """

    key: ClassVar[str]
    allows_draws: ClassVar[bool]
    locks_results: ClassVar[bool]

    @abstractmethod
    def first_rounds(self, seeded: Sequence[PlayerId]) -> list[RoundPlan]:
        """Plan the rounds known at the start, given player IDs in seed order."""

    @abstractmethod
    def next_round(self, tournament: Tournament) -> RoundPlan | None:
        """Plan the next round, or return None if no round is added later."""
