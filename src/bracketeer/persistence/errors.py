"""Errors raised when a tournament file can't be saved or opened.

The interface shows their messages to the organizer as they are, so each
message says in plain words what went wrong (NFR-US-2).
"""


class SaveFileError(Exception):
    """A tournament file couldn't be saved or opened."""


class DamagedFileError(SaveFileError):
    """The file isn't valid JSON or isn't a valid tournament (NFR-RE-2)."""

    def __init__(self, detail: str) -> None:
        super().__init__(f"The file is damaged or isn't a Bracketeer file. {detail}")


class NewerVersionError(SaveFileError):
    """The file was saved by a newer version of Bracketeer (NFR-RE-3)."""
