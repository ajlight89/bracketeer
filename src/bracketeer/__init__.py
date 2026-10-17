"""Bracketeer: a tournament manager for game nights and small esports events."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("bracketeer")
except (
    PackageNotFoundError
):  # pragma: no cover - only when run from an uninstalled source tree
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
