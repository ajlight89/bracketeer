"""File actions: new, open, save, and save as (US-10).

Tournaments are kept in one folder (session.folder, normally
Documents\\Bracketeer). Open lists the files in it, and Save asks only for a
file name, so the organizer never has to type a path. Every action that would
replace the open tournament first asks what to do with unsaved changes
(NFR-RE-4).
"""

from datetime import datetime
from pathlib import Path

from bracketeer.app.session import ActionError, TournamentSession
from bracketeer.cli.console import Console, ask_yes_no, choose, heading, show_error
from bracketeer.cli.tables import FORMAT_NAMES, fit

FILE_EXTENSION = ".bracketeer"
MAX_FILE_NAME_LENGTH = 40
FALLBACK_NAME = "tournament"

# Characters Windows doesn't allow in a file name. Blocking / and \ also means
# a typed name can never point outside the folder (NFR-SE-5).
NOT_ALLOWED = '<>:"/\\|?*'

# Names Windows reserves for devices, with or without an extension, such as
# CON, NUL.txt, COM1, or LPT0.
RESERVED = {"CON", "PRN", "AUX", "NUL"} | {
    f"{device}{digit}" for device in ("COM", "LPT") for digit in "0123456789¹²³"
}


def new_tournament(console: Console, session: TournamentSession) -> None:
    """Create a new tournament after asking for its name and format."""
    if not ok_to_discard(console, session):
        return
    name = console.ask("Tournament name (Enter to cancel): ")
    if not name:
        return
    console.say("Format:")
    keys = list(FORMAT_NAMES)
    choice = choose(console, [FORMAT_NAMES[key] for key in keys], back="Cancel")
    if choice is None:
        return
    session.new(name, keys[choice])
    console.say(f"Created {session.tournament.name}. Add the players next.")


def open_tournament(console: Console, session: TournamentSession) -> None:
    """Open a tournament chosen from the folder's list (US-10 #3)."""
    if not ok_to_discard(console, session):
        return
    path = choose_saved_file(console, session.folder)
    if path is None:
        return
    session.open(path)
    console.say(f"Opened {session.tournament.name} from {path.name}.")


def choose_saved_file(console: Console, folder: Path) -> Path | None:
    """List the saved tournaments, newest first; None if the organizer cancels.

    The last choice opens a file from another folder by its path, such as a
    file someone sent by email.
    """
    heading(console, "Open a tournament")
    files = saved_files(folder)
    if files:
        console.say(f"Saved in {folder}:")
    else:
        console.say(f"There are no saved tournaments in {folder} yet.")
    labels = [file_label(path) for path in files]
    labels.append("Open a file from another folder (type its path)")
    choice = choose(console, labels, back="Cancel")
    if choice is None:
        return None
    if choice < len(files):
        return files[choice]
    return ask_path(console, "File to open")


def saved_files(folder: Path) -> list[Path]:
    """Return the tournament files in folder, most recently saved first."""
    if not folder.is_dir():
        return []
    files = [path for path in folder.glob(f"*{FILE_EXTENSION}") if path.is_file()]
    return sorted(files, key=lambda path: path.stat().st_mtime, reverse=True)


def file_label(path: Path) -> str:
    """Return a file's name and when it was last saved, for the Open list."""
    saved = datetime.fromtimestamp(path.stat().st_mtime)
    name = fit(path.stem, MAX_FILE_NAME_LENGTH)
    return f"{name:<{MAX_FILE_NAME_LENGTH}}  saved {saved:%Y-%m-%d %H:%M}"


def save(console: Console, session: TournamentSession) -> bool:
    """Save to the tournament's file, or ask for a name. Return True if saved."""
    if session.path is None:
        return save_as(console, session)
    return _save_to(console, session, session.path)


def save_as(console: Console, session: TournamentSession) -> bool:
    """Save under a file name in the folder. Return True if saved.

    An existing file is replaced only after the organizer confirms (NFR-SE-5).
    """
    path = ask_file_name(console, session)
    if path is None:
        return False
    if path.exists() and not ask_yes_no(
        console, f"{path.name} already exists. Replace it?"
    ):
        return False
    return _save_to(console, session, path)


def ask_file_name(console: Console, session: TournamentSession) -> Path | None:
    """Ask for a file name in the folder; Enter takes the suggested name.

    The suggestion is the tournament's name with any characters Windows
    doesn't allow removed. Typing 0 cancels.
    """
    suggestion = suggested_name(session.tournament.name)
    while True:
        answer = console.ask(f"File name (Enter for {suggestion}, 0 to cancel): ")
        if answer == "0":
            return None
        name = clean_name(answer or suggestion)
        problem = name_problem(name)
        if problem is None:
            return session.folder / f"{name}{FILE_EXTENSION}"
        console.say(problem)


def suggested_name(tournament_name: str) -> str:
    """Return a safe file name based on the tournament's name."""
    kept = "".join(
        character
        for character in tournament_name
        if character not in NOT_ALLOWED and character.isprintable()
    )
    name = clean_name(kept[:MAX_FILE_NAME_LENGTH])
    return FALLBACK_NAME if name_problem(name) else name


def clean_name(text: str) -> str:
    """Drop a typed .bracketeer and the spaces and dots Windows ignores at the end."""
    name = text.strip()
    if name.lower().endswith(FILE_EXTENSION):
        name = name[: -len(FILE_EXTENSION)]
    return name.rstrip(". ")


def name_problem(name: str) -> str | None:
    """Return why a file name can't be used, or None if it's fine."""
    if not name:
        return "Type a file name, such as friday."
    if len(name) > MAX_FILE_NAME_LENGTH:
        return f"A file name can be at most {MAX_FILE_NAME_LENGTH} characters long."
    if any(c in NOT_ALLOWED or not c.isprintable() for c in name):
        return f"A file name can't contain any of these characters: {NOT_ALLOWED}"
    if name.split(".")[0].upper() in RESERVED:
        return f"Windows reserves the name {name}. Choose another name."
    return None


def ok_to_discard(console: Console, session: TournamentSession) -> bool:
    """Offer to save unsaved changes. Return False if the organizer cancels."""
    if not session.has_unsaved_changes:
        return True
    console.say("The tournament has unsaved changes.")
    choice = choose(console, ["Save them first", "Discard them"], back="Cancel")
    if choice is None:
        return False
    if choice == 0:
        return save(console, session)
    return True


def ask_path(console: Console, prompt: str) -> Path | None:
    """Ask for a full file path and return it as an absolute path; Enter cancels.

    Used only to open a file from another folder. Quotes around the path are
    removed (Windows "Copy as path" adds them), and a name with no extension
    gets ".bracketeer".
    """
    while True:
        text = console.ask(f"{prompt} (file path, Enter to cancel): ")
        text = text.strip('"').strip()
        if not text:
            return None
        path = Path(text).expanduser()
        if path.name in ("", ".", "..") or path.is_dir():
            console.say("That's a folder. Type the path of a .bracketeer file.")
            continue
        if not path.suffix:
            path = path.with_name(path.name + FILE_EXTENSION)
        # Absolute, so messages show exactly where the file is.
        return path.absolute()


def _save_to(console: Console, session: TournamentSession, path: Path) -> bool:
    """Save, creating the folder the first time. Return True if saved."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        reason = error.strerror or error
        show_error(console, f"Couldn't create the folder {path.parent}: {reason}.")
        return False
    try:
        session.save(path)
    except ActionError as error:
        show_error(console, error)
        return False
    console.say(f"Saved to {path}.")
    return True
