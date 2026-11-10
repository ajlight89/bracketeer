"""Exceptions raised when a tournament rule is broken.

Every rule violation in the domain raises a subclass of DomainError, so the
app layer can catch them all in one place and show a friendly message
(NFR-US-2). New subclasses are added as the rules that need them are built.
"""


class DomainError(Exception):
    """Base class for every rule violation in the domain."""


class InvalidNameError(DomainError):
    """A player name is empty or longer than 40 characters (R-PL-2)."""


class InvalidResultError(DomainError):
    """A result has the wrong shape or an invalid game score (R-RS-1, R-RS-5)."""


class DuplicateNameError(DomainError):
    """The name is already taken in this tournament, ignoring case (R-PL-2)."""


class PlayerCountError(DomainError):
    """The tournament has too few or too many players (R-PL-1)."""


class InvalidRatingError(DomainError):
    """A rating isn't a whole number of 0 or more (R-PL-3)."""


class UnknownPlayerError(DomainError):
    """No player in the tournament has the given ID."""


class InvalidSeedingError(DomainError):
    """The seeding is missing, or a manual order is invalid (R-SD-1)."""


class NotInMatchError(DomainError):
    """The player isn't one of the match's two players (R-RS-5)."""


class TournamentStartedError(DomainError):
    """The action isn't allowed once the tournament has started (R-PL-4, R-SD-3)."""
