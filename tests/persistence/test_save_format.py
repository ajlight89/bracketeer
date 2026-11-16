"""Tests for turning a tournament into saved data and replaying it (US-10)."""

import copy
import re

import pytest

from bracketeer.domain.errors import ResultLockedError
from bracketeer.domain.formats.single_elimination import SingleElimination
from bracketeer.domain.tournament import Tournament
from bracketeer.domain.values import Result
from bracketeer.persistence.errors import DamagedFileError
from bracketeer.persistence.save_format import (
    FORMAT_VERSION,
    tournament_from_data,
    tournament_to_data,
)

DELETE = object()


def reopened(tournament):
    """Save a tournament to data and rebuild it, as opening a file does."""
    return tournament_from_data(tournament_to_data(tournament))


def changed(data, path, value):
    """Return a copy of data with the value at path replaced, or deleted."""
    data = copy.deepcopy(data)
    *parents, last = path
    target = data
    for key in parents:
        target = target[key]
    if value is DELETE:
        del target[last]
    else:
        target[last] = value
    return data


def finish_last_round(tournament):
    """Record a 2-0 win for player A in every unplayed match of the last round."""
    for match in tournament.rounds[-1].matches:
        if match.result is None:
            tournament.record_result(match.id, Result.played(2, 0))


def standings_by_name(tournament):
    """Return the standings with names in place of IDs, which can change."""
    return [
        (tournament.player(s.player_id).name.text, s.rank, s.wins, s.losses)
        for s in tournament.standings()
    ]


# Round trips: the tournament comes back exactly as it was.


def test_a_round_robin_comes_back_exactly_as_it_was(league):
    # US-10 #1
    loaded = reopened(league)
    assert tournament_to_data(loaded) == tournament_to_data(league)
    assert loaded.standings() == league.standings()


def test_a_bracket_comes_back_exactly_as_it_was(bracket):
    # US-10 #1
    loaded = reopened(bracket)
    assert tournament_to_data(loaded) == tournament_to_data(bracket)
    assert loaded.standings() == bracket.standings()


def test_results_a_later_round_depends_on_stay_locked(bracket):
    # US-07 #5, R-RS-7
    loaded = reopened(bracket)
    with pytest.raises(ResultLockedError):
        loaded.clear_result(loaded.rounds[0].matches[0].id)


def test_a_finished_bracket_is_still_complete(bracket):
    finish_last_round(bracket)
    bracket.generate_next_round()
    finish_last_round(bracket)
    loaded = reopened(bracket)
    assert loaded.is_complete()
    assert loaded.standings() == bracket.standings()


def test_a_tournament_that_hasnt_started_comes_back(tournament):
    tournament.add_player("Ana", 1500)
    tournament.add_player("Ben")
    loaded = reopened(tournament)
    assert not loaded.started
    assert tournament_to_data(loaded) == tournament_to_data(tournament)


def test_seeds_come_back_before_the_start(tournament):
    tournament.add_player("Ana")
    tournament.add_player("Ben", 1500)
    tournament.seed_by_rating()
    loaded = reopened(tournament)
    assert [p.seed for p in loaded.players] == [2, 1]


def test_players_are_renumbered_but_nothing_else_changes():
    # A player removed before the start leaves a gap in the saved IDs.
    tournament = Tournament("Cup Night", SingleElimination())
    ids = [tournament.add_player(name) for name in ["Ana", "Ben", "Cleo", "Dev"]]
    tournament.remove_player(ids[1])
    tournament.seed_manually([ids[3], ids[0], ids[2]])
    tournament.start()
    tournament.rename_player(ids[2], "Cleo M.")
    finish_last_round(tournament)
    data = tournament_to_data(tournament)
    assert [p["id"] for p in data["players"]] == [1, 3, 4]
    loaded = tournament_from_data(data)
    assert [p.id for p in loaded.players] == [1, 2, 3]
    assert standings_by_name(loaded) == standings_by_name(tournament)


def test_saved_data_records_the_file_format_version(league):
    # NFR-RE-3
    assert tournament_to_data(league)["format_version"] == FORMAT_VERSION


# Damaged data: every problem is reported, never a crash (US-10 #4, NFR-RE-2).

DAMAGED = [
    pytest.param(
        ["format_version"], DELETE, '"format_version" is missing', id="no-version"
    ),
    pytest.param(["format_version"], "1", "format_version should", id="version-text"),
    pytest.param(["format_version"], True, "format_version should", id="version-bool"),
    pytest.param(["format_version"], 0, "format_version should", id="version-0"),
    pytest.param(["name"], 42, "name should be text", id="name-number"),
    pytest.param(["format"], "swiss", "Unknown tournament format", id="format"),
    pytest.param(["started"], "yes", "started should be true or false", id="started"),
    pytest.param(["started"], False, "hasn't started has no rounds", id="not-started"),
    pytest.param(["players"], {}, "players should be a list", id="players-object"),
    pytest.param(["players"], [], "at least 2 players", id="no-players"),
    pytest.param(["players", 0], "Ana", "players[0] should be an object", id="player"),
    pytest.param(["players", 0, "id"], "1", "players[0].id should", id="id-text"),
    pytest.param(["players", 1, "id"], 1, "Two players have the ID 1", id="id-twice"),
    pytest.param(["players", 0, "name"], None, "players[0].name should", id="no-name"),
    pytest.param(["players", 0, "name"], "  ", "1 to 40 characters", id="blank-name"),
    pytest.param(["players", 1, "name"], "ANA", "already taken", id="same-name"),
    pytest.param(["players", 0, "rating"], -5, "players[0].rating", id="rating"),
    pytest.param(["players", 0, "rating"], 1.5, "players[0].rating", id="rating-float"),
    pytest.param(["players", 0, "seed"], None, "The seeds should", id="seed-missing"),
    pytest.param(["players", 0, "seed"], 9, "The seeds should", id="seed-gap"),
    pytest.param(["players", 0, "seed"], DELETE, '"seed" is missing', id="no-seed"),
    pytest.param(["rounds"], [], "The file has 0 rounds", id="no-rounds"),
    pytest.param(["rounds", 0, "number"], 2, "Round 1 in the file", id="number"),
    pytest.param(["rounds", 0, "byes"], [], "Round 1 in the file", id="byes"),
    pytest.param(["rounds", 0, "byes", 0], 99, "refers to player 99", id="bye-who"),
    pytest.param(
        ["rounds", 0, "matches"], "x", "matches should be a list", id="matches"
    ),
    pytest.param(["rounds", 0, "matches", 0, "id"], 99, "Round 1 in", id="match-id"),
    pytest.param(
        ["rounds", 0, "matches", 0, "result"], "2-1", "should be an object", id="result"
    ),
    pytest.param(
        ["rounds", 0, "matches", 0, "result", "kind"],
        "won",
        'should be "played" or "forfeit"',
        id="kind",
    ),
    pytest.param(
        ["rounds", 0, "matches", 0, "result", "score_a"],
        -1,
        "score_a should be a whole number",
        id="score",
    ),
    pytest.param(
        ["rounds", 0, "matches", 1, "result", "forfeited_by"],
        99,
        "refers to player 99",
        id="forfeit-who",
    ),
]


@pytest.mark.parametrize(("path", "value", "message"), DAMAGED)
def test_damaged_data_is_refused_with_a_message(league, path, value, message):
    # US-10 #4, NFR-RE-2
    data = changed(tournament_to_data(league), path, value)
    with pytest.raises(DamagedFileError, match=re.escape(message)):
        tournament_from_data(data)


@pytest.mark.parametrize("data", [[], "text", None, 42])
def test_data_that_isnt_an_object_is_refused(data):
    # US-10 #4, NFR-RE-2
    with pytest.raises(DamagedFileError, match="^The file is damaged"):
        tournament_from_data(data)


def test_a_match_with_different_players_is_refused(league):
    data = tournament_to_data(league)
    sitting_out = data["rounds"][0]["byes"][0]
    data["rounds"][0]["matches"][0]["player_a"] = sitting_out
    with pytest.raises(DamagedFileError, match="Round 1 in the file"):
        tournament_from_data(data)


def test_a_forfeit_by_a_player_not_in_the_match_is_refused(league):
    data = tournament_to_data(league)
    sitting_out = data["rounds"][0]["byes"][0]
    data["rounds"][0]["matches"][1]["result"]["forfeited_by"] = sitting_out
    with pytest.raises(DamagedFileError, match="isn't in match"):
        tournament_from_data(data)


def test_an_extra_round_is_refused(league):
    for round_ in league.rounds:
        for match in round_.matches:
            if match.result is None:
                league.record_result(match.id, Result.played(2, 0))
    data = tournament_to_data(league)
    data["rounds"].append(data["rounds"][-1])
    with pytest.raises(DamagedFileError, match="no next round"):
        tournament_from_data(data)


def test_a_draw_in_a_bracket_is_refused(bracket):
    # US-07 #3, R-RS-2
    data = tournament_to_data(bracket)
    data["rounds"][1]["matches"][0]["result"] = {
        "kind": "played",
        "score_a": 2,
        "score_b": 2,
    }
    with pytest.raises(DamagedFileError, match="equal scores"):
        tournament_from_data(data)


def test_a_round_after_an_unfinished_round_is_refused(bracket):
    # R-RD-1
    data = tournament_to_data(bracket)
    data["rounds"][0]["matches"][0]["result"] = None
    with pytest.raises(DamagedFileError, match="Every match needs a result"):
        tournament_from_data(data)
