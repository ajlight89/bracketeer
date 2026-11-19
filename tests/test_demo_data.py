"""The demo data script makes every file it promises, in the promised state.

The report's screenshots rely on these files, so a rule change that breaks
them should fail here first.
"""

import importlib.util
from pathlib import Path

import pytest

from bracketeer.app.session import DEFAULT_FOLDER
from bracketeer.domain.values import ResultKind
from bracketeer.persistence.repository import TournamentRepository

SCRIPT = Path(__file__).parents[1] / "scripts" / "make_demo_data.py"


def load_script():
    """Import the script by its path; scripts/ isn't a package."""
    spec = importlib.util.spec_from_file_location("make_demo_data", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


demo = load_script()


@pytest.fixture(scope="module")
def folder(tmp_path_factory):
    """Run the script once into a temporary folder, never into Documents."""
    folder = tmp_path_factory.mktemp("demo")
    assert demo.main(["--folder", str(folder)]) == 0
    return folder


def open_demo(folder, name):
    return TournamentRepository().load(folder / f"{name}{demo.FILE_EXTENSION}")


def names(tournament, standings):
    return [tournament.player(row.player_id).name.text for row in standings]


def test_every_demo_file_is_written(folder):
    written = sorted(path.name for path in folder.glob("*.bracketeer"))
    assert written == [
        "Campus Cup (round 2).bracketeer",
        "Campus Cup.bracketeer",
        "Game Night Signups.bracketeer",
        "Thursday League.bracketeer",
    ]


def test_campus_cup_round_2_is_in_progress_with_byes(folder):
    cup = open_demo(folder, "Campus Cup (round 2)")
    assert cup.format.key == "single_elimination"
    assert len(cup.rounds[0].byes) == 2
    assert len(cup.rounds) == 2
    assert [match.result is None for match in cup.rounds[1].matches] == [False, True]


def test_campus_cup_is_complete_with_a_forfeit(folder):
    cup = open_demo(folder, "Campus Cup")
    assert cup.is_complete()
    assert names(cup, cup.standings())[0] == "ByteKnight"
    kinds = [match.result.kind for round_ in cup.rounds for match in round_.matches]
    assert ResultKind.FORFEIT in kinds


def test_thursday_league_breaks_ties_by_differential_then_seed(folder):
    league = open_demo(folder, "Thursday League")
    standings = league.standings()
    assert league.is_complete()
    assert names(league, standings) == [
        "AceVortex",
        "TurboTaco",
        "ShadowFox",
        "QuietStorm",
        "MeteorMae",
        "RetroRaven",
    ]
    second, third, fourth, fifth = standings[1:5]
    # Same points, more game differential wins (R-TB-2).
    assert second.match_points == third.match_points == 10
    assert second.game_differential > third.game_differential
    # Same points and differential, the lower seed wins (R-TB-3).
    assert fourth.match_points == fifth.match_points == 6
    assert fourth.game_differential == fifth.game_differential
    assert league.player(fourth.player_id).seed < league.player(fifth.player_id).seed


def test_game_night_signups_is_not_seeded_or_started(folder):
    signups = open_demo(folder, "Game Night Signups")
    assert not signups.started
    assert len(signups.players) == 5
    assert all(player.seed is None for player in signups.players)
    assert any(player.rating is None for player in signups.players)


def test_existing_files_are_kept_unless_replace_is_given(tmp_path, capsys):
    kept = tmp_path / "Campus Cup.bracketeer"
    kept.write_text("an organizer's own file", encoding="utf-8")
    demo.main(["--folder", str(tmp_path)])
    assert kept.read_text(encoding="utf-8") == "an organizer's own file"
    assert "Kept" in capsys.readouterr().out
    demo.main(["--folder", str(tmp_path), "--replace"])
    assert open_demo(tmp_path, "Campus Cup").is_complete()


def test_the_default_folder_is_the_bracketeer_folder():
    # Only the arguments are parsed, so nothing is written to Documents.
    assert demo.parse_args([]).folder == DEFAULT_FOLDER
