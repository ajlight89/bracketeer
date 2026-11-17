"""Tests for TournamentSession, the app layer between the menus and the rules."""

from pathlib import Path
from random import Random

import pytest

from bracketeer.app.session import (
    DEFAULT_FOLDER,
    ActionError,
    TournamentSession,
    plain_message,
    players_by_seed,
)
from bracketeer.domain.errors import DuplicateNameError
from bracketeer.domain.tournament import Tournament


@pytest.fixture
def session():
    """A session with a new 4-player round robin, not yet seeded."""
    session = TournamentSession(rng=Random(7))
    session.new("Friday Smash Night", "round_robin")
    for name, rating in [("Ana", 1500), ("Ben", 1800), ("Cleo", None), ("Dev", 1200)]:
        session.add_player(name, rating)
    return session


@pytest.fixture
def saved(session, tmp_path):
    """The same session after saving, so it has no unsaved changes."""
    session.save(tmp_path / "friday.bracketeer")
    return session


def names(players):
    return [player.name.text for player in players]


# New, open, and save


def test_new_tournament_is_empty_unsaved_and_has_no_file():
    session = TournamentSession()
    session.new("  Cup Night  ", "single_elimination")
    assert session.tournament.name == "Cup Night"
    assert session.tournament.format.key == "single_elimination"
    assert session.tournament.players == ()
    assert session.path is None
    assert session.has_unsaved_changes


@pytest.mark.parametrize("name", ["", "   ", "x" * 41])
def test_a_tournament_name_must_be_1_to_40_characters(name):
    session = TournamentSession()
    with pytest.raises(ActionError, match="1 to 40 characters"):
        session.new(name, "round_robin")
    assert session.tournament is None


def test_an_unknown_format_is_refused_with_a_message():
    with pytest.raises(ActionError, match="Unknown tournament format"):
        TournamentSession().new("Cup Night", "swiss")


def test_tournaments_are_kept_in_documents_bracketeer_by_default():
    assert DEFAULT_FOLDER == Path.home() / "Documents" / "Bracketeer"
    assert TournamentSession().folder == DEFAULT_FOLDER


def test_a_session_can_be_given_another_folder(tmp_path):
    assert TournamentSession(folder=tmp_path).folder == tmp_path


def test_saving_records_the_file_and_clears_unsaved_changes(saved, tmp_path):
    assert saved.path == tmp_path / "friday.bracketeer"
    assert saved.path.exists()
    assert not saved.has_unsaved_changes


def test_us_10_1_a_saved_tournament_opens_exactly_as_it_was_left(saved):
    saved.seed_by_rating()
    saved.start()
    first = saved.tournament.rounds[0].matches[0]
    saved.record_score(first.id, 2, 1)
    saved.save(saved.path)

    reopened = TournamentSession()
    reopened.open(saved.path)
    assert reopened.path == saved.path
    assert not reopened.has_unsaved_changes
    assert names(reopened.tournament.players) == names(saved.tournament.players)
    assert reopened.tournament.standings() == saved.tournament.standings()


def test_a_failed_save_keeps_the_unsaved_changes(saved, tmp_path):
    saved.add_player("Eve", None)
    with pytest.raises(ActionError, match="Couldn't save"):
        saved.save(tmp_path / "missing folder" / "friday.bracketeer")
    assert saved.has_unsaved_changes
    assert saved.path == tmp_path / "friday.bracketeer"


def test_us_10_4_a_damaged_file_leaves_the_open_tournament_unchanged(saved, tmp_path):
    damaged = tmp_path / "damaged.bracketeer"
    damaged.write_text("{ not json", encoding="utf-8")
    before = saved.tournament
    with pytest.raises(ActionError, match="damaged"):
        saved.open(damaged)
    assert saved.tournament is before
    assert saved.path == tmp_path / "friday.bracketeer"


def test_actions_need_an_open_tournament():
    with pytest.raises(ActionError, match="Create or open a tournament first"):
        TournamentSession().add_player("Ana", None)


# Changes and unsaved changes (NFR-RE-4)


def test_nfr_re_4_every_change_marks_the_session_unsaved(saved):
    saved.add_player("Eve", None)
    assert saved.has_unsaved_changes


def test_a_refused_change_leaves_the_session_saved(saved):
    with pytest.raises(ActionError):
        saved.add_player("ana", None)
    assert not saved.has_unsaved_changes


def test_a_refused_change_keeps_the_domain_error_as_its_cause(session):
    with pytest.raises(ActionError) as caught:
        session.add_player("ANA", None)
    assert isinstance(caught.value.__cause__, DuplicateNameError)


def test_us_02_editing_and_removing_go_through_the_session(session):
    ana, ben = session.tournament.players[:2]
    session.edit_player(ana.id, "Anna", None)
    session.remove_player(ben.id)
    assert names(session.tournament.players) == ["Anna", "Cleo", "Dev"]
    assert ana.rating is None


def test_us_02_3_a_name_can_be_corrected_after_the_start(session):
    session.seed_by_rating()
    session.start()
    session.rename_player(session.tournament.players[0].id, "Anna")
    assert session.tournament.players[0].name.text == "Anna"


# Plain-language messages (NFR-US-2)


@pytest.mark.parametrize(
    ("message", "plain"),
    [
        ("It has started (R-PL-4, R-SD-3).", "It has started."),
        ("Enter every result first (R-RD-1).", "Enter every result first."),
        ("A rating must be 0 or more; got -5.", "A rating must be 0 or more; got -5."),
        ("Saving failed (disk full).", "Saving failed (disk full)."),
    ],
)
def test_rule_ids_are_removed_from_messages(message, plain):
    assert plain_message(Exception(message)) == plain


def test_nfr_us_2_a_refused_action_says_why_without_rule_ids(session):
    session.seed_by_rating()
    session.start()
    with pytest.raises(ActionError) as caught:
        session.add_player("Eve", None)
    assert str(caught.value) == "The tournament has already started."


# Seeding (US-03)


def test_seeding_randomly_uses_the_sessions_random_generator(session):
    session.seed_randomly()
    expected = Tournament("Copy", session.tournament.format)
    for player in session.tournament.players:
        expected.add_player(player.name.text, player.rating)
    expected.seed_randomly(Random(7))
    assert [p.seed for p in session.tournament.players] == [
        p.seed for p in expected.players
    ]


def test_us_03_4_moving_a_player_to_seed_1_shifts_the_others_down(session):
    session.seed_by_rating()  # Ben 1, Ana 2, Dev 3, Cleo 4
    dev = session.tournament.players[3]
    session.move_to_seed(dev.id, 1)
    assert names(players_by_seed(session.tournament)) == ["Dev", "Ben", "Ana", "Cleo"]
    assert sorted(p.seed for p in session.tournament.players) == [1, 2, 3, 4]


def test_moving_an_unseeded_player_seeds_the_rest_in_registration_order(session):
    cleo = session.tournament.players[2]
    session.move_to_seed(cleo.id, 1)
    assert names(players_by_seed(session.tournament)) == ["Cleo", "Ana", "Ben", "Dev"]


@pytest.mark.parametrize("seed", [0, 5])
def test_moving_to_a_seed_outside_1_to_n_is_refused(session, seed):
    with pytest.raises(ActionError, match="from 1 to 4"):
        session.move_to_seed(session.tournament.players[0].id, seed)


def test_players_by_seed_keeps_registration_order_before_seeding(session):
    assert names(players_by_seed(session.tournament)) == ["Ana", "Ben", "Cleo", "Dev"]


# Results and rounds (US-04, US-07)


@pytest.fixture
def cup():
    """A started 4-player single elimination: Ana v Dev and Ben v Cleo."""
    session = TournamentSession()
    session.new("Cup Night", "single_elimination")
    for name in ["Ana", "Ben", "Cleo", "Dev"]:
        session.add_player(name, None)
    session.move_to_seed(1, 1)  # seeds in registration order
    session.start()
    return session


def test_us_07_3_a_draw_in_single_elimination_is_refused(cup):
    match = cup.tournament.rounds[0].matches[0]
    with pytest.raises(ActionError, match="needs a winner in every match"):
        cup.record_score(match.id, 2, 2)
    assert match.result is None


def test_us_04_a_bracket_runs_to_a_champion_through_the_session(cup):
    first, second = cup.tournament.rounds[0].matches
    cup.record_score(first.id, 2, 0)
    cup.record_forfeit(second.id, second.player_b)
    cup.generate_next_round()
    final = cup.tournament.rounds[1].matches[0]
    cup.record_score(final.id, 1, 3)
    assert cup.tournament.is_complete()
    champion = cup.tournament.standings()[0].player_id
    assert cup.tournament.player(champion).name.text == "Ben"


def test_us_07_5_a_locked_result_is_refused_with_a_message(cup):
    first, second = cup.tournament.rounds[0].matches
    cup.record_score(first.id, 2, 0)
    cup.record_score(second.id, 2, 0)
    cup.generate_next_round()
    with pytest.raises(ActionError, match="next round depends on it"):
        cup.clear_result(first.id)


def test_us_07_7_clearing_a_result_makes_the_match_unplayed(cup):
    match = cup.tournament.rounds[0].matches[0]
    cup.record_score(match.id, 2, 0)
    cup.clear_result(match.id)
    assert match.result is None


# Exporting a web page (US-11)


def test_us_11_1_export_writes_a_utf_8_web_page(session, tmp_path):
    session.rename_player(1, "Zoë")
    session.seed_by_rating()
    session.start()
    session.save(tmp_path / "friday.bracketeer")
    page = tmp_path / "friday.html"
    session.export_web_page(page)
    assert "Zoë" in page.read_text(encoding="utf-8")
    assert not session.has_unsaved_changes  # exporting changes nothing


def test_exporting_before_the_start_is_refused(session, tmp_path):
    with pytest.raises(ActionError, match="Start the tournament before exporting"):
        session.export_web_page(tmp_path / "friday.html")
    assert not (tmp_path / "friday.html").exists()


def test_a_page_that_cant_be_written_raises_a_plain_message(cup, tmp_path):
    with pytest.raises(ActionError, match="Couldn't export to"):
        cup.export_web_page(tmp_path / "missing" / "cup.html")
