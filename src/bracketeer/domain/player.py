"""The Player entity."""

from dataclasses import dataclass

from bracketeer.domain.values import PlayerId, PlayerName


@dataclass(eq=False)
class Player:
    """A registered participant (docs/design.md).

    Player is an entity: it keeps its identity while its name, rating, and
    seed change, so == compares identity, not values. IDs are given out in
    registration order and never reused, so sorting by ID gives the
    registration order (R-SD-2).
    """

    id: PlayerId
    name: PlayerName
    rating: int | None = None
    seed: int | None = None
