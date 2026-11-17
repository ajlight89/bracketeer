"""Tests for the file actions: the folder, file names, open, save (US-10)."""

import os

import pytest

from bracketeer.app.session import TournamentSession
from bracketeer.cli.files import (
    ask_path,
    clean_name,
    export_web_page,
    name_problem,
    save,
    save_as,
    saved_files,
    suggested_name,
)
from bracketeer.cli.menus import run


def saved_file(folder, name, age_in_minutes, text="{}"):
    """Write a file into folder that was last changed some minutes ago."""
    folder.mkdir(exist_ok=True)
    path = folder / name
    path.write_text(text, encoding="utf-8")
    when = path.stat().st_mtime - age_in_minutes * 60
    os.utime(path, (when, when))
    return path


# File names (NFR-SE-5)


@pytest.mark.parametrize(
    ("tournament_name", "suggestion"),
    [
        ("Friday Smash Night", "Friday Smash Night"),
        ("Finals: Who Wins?", "Finals Who Wins"),
        ("???", "tournament"),
        ("CON", "tournament"),
        ("Cup...", "Cup"),
    ],
)
def test_the_suggested_name_drops_characters_windows_does_not_allow(
    tournament_name, suggestion
):
    assert suggested_name(tournament_name) == suggestion


def test_a_typed_extension_and_trailing_dots_are_dropped():
    assert clean_name(" friday.bracketeer ") == "friday"
    assert clean_name("friday.") == "friday"


@pytest.mark.parametrize(
    ("name", "problem"),
    [
        ("", "Type a file name"),
        ("x" * 41, "at most 40 characters"),
        ("..\\..\\Windows\\cup", "can't contain"),
        ("../cup", "can't contain"),
        ("a:b", "can't contain"),
        ("nul", "Windows reserves"),
        ("COM1.backup", "Windows reserves"),
        ("lpt0", "Windows reserves"),
    ],
)
def test_nfr_se_5_unsafe_file_names_are_refused(name, problem):
    assert problem in name_problem(name)


def test_an_ordinary_file_name_is_accepted():
    assert name_problem("Friday Smash Night 2") is None


# Saving


def test_the_first_save_suggests_the_tournament_name_and_makes_the_folder(
    script, league, folder
):
    assert not folder.exists()
    console = script("")
    assert save(console, league)
    assert league.path == folder / "Friday Smash Night.bracketeer"
    assert league.path.exists()
    assert f"Saved to {league.path}." in console.screen


def test_save_as_uses_the_typed_name_in_the_folder(script, league, folder):
    assert save_as(script("friday"), league)
    assert league.path == folder / "friday.bracketeer"


def test_a_bad_file_name_is_asked_again(script, league, folder):
    console = script("../friday", "friday")
    assert save_as(console, league)
    assert "can't contain" in console.screen
    assert league.path == folder / "friday.bracketeer"


def test_typing_0_cancels_saving(script, league, folder):
    assert not save_as(script("0"), league)
    assert league.path is None
    assert not folder.exists()


def test_save_uses_the_tournaments_file_without_asking(script, league, folder):
    save_as(script("friday"), league)
    league.add_player("Dev", None)
    assert save(script(), league)
    assert not league.has_unsaved_changes


def test_nfr_se_5_an_existing_file_is_replaced_only_after_confirming(
    script, cup, folder
):
    existing = saved_file(folder, "cup.bracketeer", 5, text="keep me")
    assert not save_as(script("cup", "n"), cup)
    assert existing.read_text(encoding="utf-8") == "keep me"
    assert save_as(script("cup", "y"), cup)
    assert '"name": "Cup Night"' in existing.read_text(encoding="utf-8")


def test_a_folder_that_cant_be_made_shows_a_message(script, league, tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("a file, not a folder", encoding="utf-8")
    league.folder = blocker / "Bracketeer"
    console = script("")
    assert not save(console, league)
    assert "Error: Couldn't create the folder" in console.screen
    assert league.has_unsaved_changes


# Opening (US-10 #3 to #5)


def test_saved_files_lists_only_tournaments_newest_first(folder):
    saved_file(folder, "old.bracketeer", 60)
    saved_file(folder, "new.bracketeer", 1)
    saved_file(folder, "notes.txt", 0)
    assert [path.name for path in saved_files(folder)] == [
        "new.bracketeer",
        "old.bracketeer",
    ]


def test_saved_files_is_empty_before_the_folder_exists(folder):
    assert saved_files(folder) == []


def test_us_10_3_open_lists_the_saved_tournaments_to_choose_from(
    script, league, folder
):
    save_as(script("friday"), league)
    os.utime(league.path, (1, 1))  # saved long ago, so it's listed second
    session = TournamentSession()
    session.new("Cup Night", "single_elimination")
    save_as(script("cup"), session)

    opener = TournamentSession()
    console = script("2", "2", "0")  # Open, the second file, Quit
    assert run(console, opener) == 0
    assert "  1. cup " in console.screen
    assert "  2. friday " in console.screen
    assert opener.tournament.name == "Friday Smash Night"
    assert opener.path == folder / "friday.bracketeer"


def test_us_10_3_choosing_0_returns_to_the_menu_with_nothing_changed(script):
    session = TournamentSession()
    console = script("2", "0", "0")
    assert run(console, session) == 0
    assert "There are no saved tournaments in" in console.screen
    assert session.tournament is None


def test_a_file_from_another_folder_can_be_opened_by_its_path(script, league, tmp_path):
    elsewhere = tmp_path / "Downloads"
    elsewhere.mkdir()
    league.save(elsewhere / "sent.bracketeer")
    session = TournamentSession()
    console = script("2", "1", f'"{elsewhere / "sent"}"', "0")
    run(console, session)
    assert session.path == elsewhere / "sent.bracketeer"


def test_us_10_4_a_damaged_file_shows_a_message_and_is_not_changed(script, folder):
    damaged = saved_file(folder, "damaged.bracketeer", 1, '{"format_version": 1,')
    console = script("2", "1", "0")
    assert run(console, TournamentSession()) == 0
    assert "Error: The file is damaged or isn't a Bracketeer file." in console.screen
    assert damaged.read_text(encoding="utf-8") == '{"format_version": 1,'


def test_us_10_5_a_newer_file_is_refused_with_a_message(script, folder):
    saved_file(folder, "newer.bracketeer", 1, '{"format_version": 99}')
    console = script("2", "1", "0")
    run(console, TournamentSession())
    assert "newer version" in console.screen


# Typed paths, for files in another folder


def test_a_typed_path_without_an_extension_gets_bracketeer(script, tmp_path):
    path = ask_path(script(str(tmp_path / "friday")), "File to open")
    assert path == tmp_path / "friday.bracketeer"


def test_a_relative_path_becomes_absolute(script, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert ask_path(script("cup"), "File to open") == tmp_path / "cup.bracketeer"


def test_a_typed_folder_is_refused_until_a_file_is_typed(script, tmp_path):
    console = script(str(tmp_path), str(tmp_path / "cup"))
    assert ask_path(console, "File to open") == tmp_path / "cup.bracketeer"
    assert "That's a folder" in console.screen


# Unsaved changes (US-10 #2, NFR-RE-4)


def test_us_10_2_quitting_with_unsaved_changes_asks_first(script, league):
    console = script("0", "0", "0", "2")  # quit, cancel, quit, discard
    assert run(console, league) == 0
    assert console.screen.count("The tournament has unsaved changes.") == 2


def test_us_10_2_saving_first_saves_then_quits(script, league, folder):
    console = script("0", "1", "")  # quit, save first, suggested name
    assert run(console, league) == 0
    assert (folder / "Friday Smash Night.bracketeer").exists()


def test_a_failed_save_while_quitting_does_not_quit(script, league, tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("a file, not a folder", encoding="utf-8")
    league.folder = blocker / "Bracketeer"
    console = script("0", "1", "", "0", "2")
    assert run(console, league) == 0
    assert "Error: Couldn't create the folder" in console.screen
    assert console.screen.count("The tournament has unsaved changes.") == 2


@pytest.mark.parametrize("choice", ["5", "6"])  # New tournament, Open a tournament
def test_us_10_2_new_and_open_ask_before_discarding(script, league, choice):
    console = script(choice, "0", "0", "2")  # ..., cancel, quit, discard
    run(console, league)
    assert league.tournament.name == "Friday Smash Night"
    assert console.screen.count("The tournament has unsaved changes.") == 2


# Exporting a web page (US-11 #4)


def test_us_11_4_export_suggests_the_tournament_name_in_the_folder(script, cup, folder):
    console = script("")
    assert export_web_page(console, cup)
    page = folder / "Cup Night.html"
    assert page.exists()
    assert f"Exported to {page}." in console.screen
    assert "Open it in a web browser" in console.screen


def test_us_11_4_export_refuses_a_name_that_leaves_the_folder(script, cup, folder):
    console = script("..\\results", "results.html")
    assert export_web_page(console, cup)
    assert "can't contain" in console.screen
    assert sorted(path.name for path in folder.iterdir()) == ["results.html"]


def test_us_11_4_an_existing_page_is_replaced_only_after_confirming(
    script, cup, folder
):
    existing = saved_file(folder, "cup.html", 5, text="keep me")
    assert not export_web_page(script("cup", "n"), cup)
    assert existing.read_text(encoding="utf-8") == "keep me"
    assert export_web_page(script("cup", "y"), cup)
    assert "Cup Night" in existing.read_text(encoding="utf-8")


def test_typing_0_cancels_exporting(script, cup, folder):
    assert not export_web_page(script("0"), cup)
    assert not folder.exists()


def test_exporting_keeps_the_tournament_and_its_unsaved_changes_flag(script, cup):
    assert cup.has_unsaved_changes
    export_web_page(script(""), cup)
    assert cup.has_unsaved_changes
    assert cup.path is None


def test_a_page_that_cant_be_written_shows_a_message(script, cup, folder):
    (folder / "cup.html").mkdir(parents=True)  # a folder where the file should go
    console = script("cup", "y")
    assert not export_web_page(console, cup)
    assert "Error: Couldn't export to" in console.screen
