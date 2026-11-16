"""A scripted console, so menu tests run without a keyboard."""

import pytest

from bracketeer.app import session as session_module
from bracketeer.app.session import TournamentSession
from bracketeer.cli.console import Console


class ScriptedConsole(Console):
    """Answers each prompt with the next scripted answer and records the screen.

    Running out of answers fails the test, so a menu that loops forever, or
    asks a question the test didn't expect, can't hang the test run.
    """

    def __init__(self, *answers: str) -> None:
        self.answers = list(answers)
        self.lines: list[str] = []

    def ask(self, prompt: str) -> str:
        if not self.answers:
            raise AssertionError(f"No scripted answer left for {prompt!r}")
        answer = self.answers.pop(0)
        self.lines.append(prompt + answer)
        return answer.strip()

    def say(self, text: str = "") -> None:
        self.lines.extend(text.split("\n"))

    @property
    def screen(self) -> str:
        return "\n".join(self.lines)


@pytest.fixture(autouse=True)
def folder(tmp_path, monkeypatch):
    """The tournaments folder for each test: a new temporary folder.

    autouse=True applies it to every test here, so no test can read or write
    the real Documents\\Bracketeer folder.
    """
    test_folder = tmp_path / "Bracketeer"
    monkeypatch.setattr(session_module, "DEFAULT_FOLDER", test_folder)
    return test_folder


@pytest.fixture
def script():
    """Make a scripted console: script("1", "Ana") answers "1", then "Ana"."""
    return ScriptedConsole


@pytest.fixture
def league():
    """A new 3-player round robin with unsaved changes: Ana, Ben, and Cleo."""
    session = TournamentSession()
    session.new("Friday Smash Night", "round_robin")
    session.add_player("Ana", 1500)
    session.add_player("Ben", 1800)
    session.add_player("Cleo", None)
    return session


@pytest.fixture
def cup():
    """A started 4-player single elimination: Ana v Dev and Ben v Cleo."""
    session = TournamentSession()
    session.new("Cup Night", "single_elimination")
    for name in ["Ana", "Ben", "Cleo", "Dev"]:
        session.add_player(name, None)
    session.move_to_seed(1, 1)
    session.start()
    return session
