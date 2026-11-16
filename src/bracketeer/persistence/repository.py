"""TournamentRepository: the only code that reads or writes tournament files."""

import json
import os
import tempfile
from pathlib import Path

from bracketeer.domain.tournament import Tournament
from bracketeer.persistence.errors import DamagedFileError, SaveFileError
from bracketeer.persistence.save_format import tournament_from_data, tournament_to_data


class TournamentRepository:
    """Saves tournaments as JSON files and opens them again (docs/design.md).

    The rest of the app calls save() and load() and never handles JSON or
    files itself (Repository pattern), so the storage could change without
    touching the rules or the interface.
    """

    def save(self, tournament: Tournament, path: Path) -> None:
        """Write the tournament to path, replacing any file already there.

        The data goes to a temporary file in the same folder, which then
        replaces the old file in one step, so a failed save never leaves a
        half-written file (NFR-RE-1). Raises SaveFileError.
        """
        data = tournament_to_data(tournament)
        text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        try:
            # Same folder, so os.replace never has to move between drives.
            handle, temp_name = tempfile.mkstemp(
                dir=path.parent, prefix=f"{path.name}.", suffix=".tmp"
            )
        except OSError as error:
            raise _save_error(path, error) from error
        temp_path = Path(temp_name)
        try:
            with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as file:
                file.write(text)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temp_path, path)
        except OSError as error:
            temp_path.unlink(missing_ok=True)
            raise _save_error(path, error) from error

    def load(self, path: Path) -> Tournament:
        """Open a saved tournament. The file is only read, never changed.

        Raises SaveFileError if the file can't be read, DamagedFileError if
        it isn't a valid tournament (NFR-RE-2), and NewerVersionError if a
        newer version of Bracketeer saved it (NFR-RE-3).
        """
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            raise DamagedFileError("It isn't a text file.") from error
        except OSError as error:
            raise SaveFileError(f"Couldn't open {path}: {_reason(error)}.") from error
        try:
            # json only builds dicts, lists, text, and numbers: never code
            # (NFR-SE-4). Very deep nesting raises RecursionError.
            data = json.loads(text)
        except json.JSONDecodeError as error:
            raise DamagedFileError(
                f"It isn't valid JSON (line {error.lineno}, column {error.colno})."
            ) from error
        except RecursionError as error:
            raise DamagedFileError("It's nested too deeply to read.") from error
        return tournament_from_data(data)


def _save_error(path: Path, error: OSError) -> SaveFileError:
    return SaveFileError(f"Couldn't save to {path}: {_reason(error)}.")


def _reason(error: OSError) -> str:
    """Return the operating system's reason, such as 'No such file or directory'."""
    return error.strerror or str(error)
