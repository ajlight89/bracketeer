"""TournamentSession: the interface's single way to change the tournament."""

import re
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from random import Random

from bracketeer.domain.errors import DomainError
from bracketeer.domain.formats.registry import format_for
from bracketeer.domain.player import Player
from bracketeer.domain.tournament import Tournament
from bracketeer.domain.values import MatchId, PlayerId, Result
from bracketeer.export.web_page import write_web_page
from bracketeer.persistence.errors import SaveFileError
from bracketeer.persistence.repository import TournamentRepository

MAX_TOURNAMENT_NAME_LENGTH = 40

# Where tournament files are kept unless the session is given another folder.
DEFAULT_FOLDER = Path.home() / "Documents" / "Bracketeer"

# Domain messages end with the rules they enforce, such as "(R-RS-7)". Those
# IDs help developers and tests, but mean nothing to an organizer.
RULE_REFERENCE = re.compile(r" \((?:NFR|R)-[A-Z]{2}-\d+(?:, (?:NFR|R)-[A-Z]{2}-\d+)*\)")


class ActionError(Exception):
    """An action was refused; the message says why in plain words (NFR-US-2)."""


class TournamentSession:
    """The open tournament, its file, its folder, and unsaved changes.

    The interface reads session.tournament to display it, but changes it only
    through these methods. Each method that succeeds marks the session as
    having unsaved changes, so the interface can ask before discarding them
    (NFR-RE-4). Rule violations and file problems come out as ActionError, so
    the interface catches one exception type.
    """

    def __init__(
        self,
        repository: TournamentRepository | None = None,
        rng: Random | None = None,
        folder: Path | None = None,
    ) -> None:
        self._repository = repository or TournamentRepository()
        # Passed in so tests can fix the seed of random seeding.
        self._rng = rng or Random()
        # The interface saves new files here and lists this folder to open one.
        self.folder = folder or DEFAULT_FOLDER
        self.tournament: Tournament | None = None
        self.path: Path | None = None
        self.has_unsaved_changes = False

    def new(self, name: str, format_key: str) -> None:
        """Replace the open tournament with a new, empty one."""
        name = name.strip()
        if not 1 <= len(name) <= MAX_TOURNAMENT_NAME_LENGTH:
            raise ActionError(
                f"A tournament name must be 1 to {MAX_TOURNAMENT_NAME_LENGTH} "
                "characters long."
            )
        with _plain_errors():
            tournament_format = format_for(format_key)
        self.tournament = Tournament(name, tournament_format)
        self.path = None
        self.has_unsaved_changes = True

    def open(self, path: Path) -> None:
        """Open a saved tournament. On failure, the open one stays as it was."""
        with _plain_errors():
            tournament = self._repository.load(path)
        self.tournament = tournament
        self.path = path
        self.has_unsaved_changes = False

    def save(self, path: Path) -> None:
        """Save the tournament to path, which becomes the file for later saves."""
        tournament = self._current()
        with _plain_errors():
            self._repository.save(tournament, path)
        self.path = path
        self.has_unsaved_changes = False

    def export_web_page(self, path: Path) -> None:
        """Write the tournament as a single web page to path (US-11).

        Exporting doesn't change the tournament, so it doesn't count as an
        unsaved change.
        """
        tournament = self._current()
        if not tournament.started:
            raise ActionError("Start the tournament before exporting it.")
        try:
            write_web_page(tournament, path, datetime.now())
        except OSError as error:
            reason = error.strerror or error
            raise ActionError(f"Couldn't export to {path}: {reason}.") from error

    def add_player(self, name: str, rating: int | None) -> PlayerId:
        with self._changing() as tournament:
            return tournament.add_player(name, rating)

    def edit_player(self, player_id: PlayerId, name: str, rating: int | None) -> None:
        with self._changing() as tournament:
            tournament.edit_player(player_id, name, rating)

    def rename_player(self, player_id: PlayerId, name: str) -> None:
        with self._changing() as tournament:
            tournament.rename_player(player_id, name)

    def remove_player(self, player_id: PlayerId) -> None:
        with self._changing() as tournament:
            tournament.remove_player(player_id)

    def seed_by_rating(self) -> None:
        with self._changing() as tournament:
            tournament.seed_by_rating()

    def seed_randomly(self) -> None:
        with self._changing() as tournament:
            tournament.seed_randomly(self._rng)

    def move_to_seed(self, player_id: PlayerId, seed: int) -> None:
        """Move one player to a seed; the others keep their order (US-03 #4).

        Unseeded players are taken in registration order first.
        """
        with self._changing() as tournament:
            order = [player.id for player in players_by_seed(tournament)]
            if not 1 <= seed <= len(order):
                raise ActionError(f"Choose a seed from 1 to {len(order)}.")
            order.remove(tournament.player(player_id).id)
            order.insert(seed - 1, player_id)
            tournament.seed_manually(order)

    def start(self) -> None:
        with self._changing() as tournament:
            tournament.start()

    def record_score(self, match_id: MatchId, score_a: int, score_b: int) -> None:
        with self._changing() as tournament:
            tournament.record_result(match_id, Result.played(score_a, score_b))

    def record_forfeit(self, match_id: MatchId, forfeited_by: PlayerId) -> None:
        with self._changing() as tournament:
            tournament.record_result(match_id, Result.forfeit(forfeited_by))

    def clear_result(self, match_id: MatchId) -> None:
        with self._changing() as tournament:
            tournament.clear_result(match_id)

    def generate_next_round(self) -> None:
        with self._changing() as tournament:
            tournament.generate_next_round()

    def _current(self) -> Tournament:
        if self.tournament is None:
            raise ActionError("Create or open a tournament first.")
        return self.tournament

    @contextmanager
    def _changing(self) -> Generator[Tournament, None, None]:
        """Run one change: plain-language errors, then mark it unsaved."""
        tournament = self._current()
        with _plain_errors():
            yield tournament
        # Reached only if the change didn't raise.
        self.has_unsaved_changes = True


def players_by_seed(tournament: Tournament) -> list[Player]:
    """Return the players by seed, or in registration order if unseeded."""
    players = list(tournament.players)
    if any(player.seed is None for player in players):
        return players
    return sorted(players, key=lambda player: player.seed)


def plain_message(error: Exception) -> str:
    """Return an error's message without the rule IDs at its end."""
    return RULE_REFERENCE.sub("", str(error))


@contextmanager
def _plain_errors() -> Generator[None, None, None]:
    """Turn rule violations and file problems into ActionError (NFR-US-2)."""
    try:
        yield
    except (DomainError, SaveFileError) as error:
        raise ActionError(plain_message(error)) from error
