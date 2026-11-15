"""Find a tournament format by its key, the name a saved file stores."""

from bracketeer.domain.errors import UnknownFormatError
from bracketeer.domain.formats.base import TournamentFormat
from bracketeer.domain.formats.round_robin import RoundRobin
from bracketeer.domain.formats.single_elimination import SingleElimination

FORMATS: dict[str, type[TournamentFormat]] = {
    RoundRobin.key: RoundRobin,
    SingleElimination.key: SingleElimination,
}


def format_for(key: object) -> TournamentFormat:
    """Return a new format object for a key, such as "round_robin"."""
    format_class = FORMATS.get(key) if isinstance(key, str) else None
    if format_class is None:
        raise UnknownFormatError(f"Unknown tournament format: {key!r}")
    return format_class()
