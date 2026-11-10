"""Value objects: small immutable types defined only by their values."""

from dataclasses import dataclass
from enum import Enum
from typing import Self

from bracketeer.domain.errors import InvalidNameError, InvalidResultError

MAX_NAME_LENGTH = 40

# Each tournament numbers its own players, starting from 1.
PlayerId = int

# Each tournament numbers its own matches, starting from 1.
MatchId = int


@dataclass(frozen=True)
class PlayerName:
    """A validated player name: trimmed, 1-40 characters (R-PL-2)."""

    text: str

    def __post_init__(self) -> None:
        trimmed = self.text.strip()
        if not 1 <= len(trimmed) <= MAX_NAME_LENGTH:
            raise InvalidNameError(
                f"A name must be 1 to {MAX_NAME_LENGTH} characters long "
                f"after trimming spaces; got {len(trimmed)}."
            )
        # A frozen dataclass blocks normal assignment, even here.
        object.__setattr__(self, "text", trimmed)

    def key(self) -> str:
        """Return the case-folded name used to check uniqueness."""
        return self.text.casefold()


class ResultKind(Enum):
    """How a match was decided."""

    PLAYED = "played"
    FORFEIT = "forfeit"


def is_non_negative_int(value: object) -> bool:
    """Return True if value is a whole number of 0 or more.

    bool is a subclass of int, so True would otherwise pass as 1.
    """
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


@dataclass(frozen=True)
class Result:
    """The outcome of one match: played with game scores, or a forfeit.

    Who won is answered by Match, which knows both players.
    """

    kind: ResultKind
    score_a: int | None = None
    score_b: int | None = None
    forfeited_by: PlayerId | None = None

    def __post_init__(self) -> None:
        if self.kind is ResultKind.PLAYED:
            if not (
                is_non_negative_int(self.score_a) and is_non_negative_int(self.score_b)
            ):
                raise InvalidResultError(
                    "Game scores must be whole numbers of 0 or more; "
                    f"got {self.score_a!r} and {self.score_b!r}."
                )
            if self.forfeited_by is not None:
                raise InvalidResultError(
                    "A played result can't name a forfeiting player."
                )
        elif self.kind is ResultKind.FORFEIT:
            if self.forfeited_by is None:
                raise InvalidResultError(
                    "A forfeit must name the player who forfeited."
                )
            if self.score_a is not None or self.score_b is not None:
                raise InvalidResultError("A forfeit has no game scores (R-RS-5).")
        else:
            raise InvalidResultError(f"Unknown result kind: {self.kind!r}.")

    @classmethod
    def played(cls, score_a: int, score_b: int) -> Self:
        """Create a played result with two game scores."""
        return cls(ResultKind.PLAYED, score_a, score_b)

    @classmethod
    def forfeit(cls, forfeited_by: PlayerId) -> Self:
        """Create a forfeit by the given player (R-RS-5)."""
        return cls(ResultKind.FORFEIT, forfeited_by=forfeited_by)

    def is_draw(self) -> bool:
        """Return True if the match was played and the scores are equal."""
        return self.kind is ResultKind.PLAYED and self.score_a == self.score_b
