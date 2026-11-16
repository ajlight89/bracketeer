"""Tests for the text tables: content, and the 80-column limit (NFR-US-3)."""

from pathlib import Path

import pytest

from bracketeer.app.session import TournamentSession
from bracketeer.cli.tables import (
    fit,
    player_lines,
    plural,
    result_text,
    round_lines,
    signed,
    standings_lines,
    status_lines,
)
from bracketeer.domain.rounds import Match
from bracketeer.domain.values import Result


def test_fit_leaves_short_text_and_cuts_long_text_with_an_ellipsis():
    assert fit("Ana", 5) == "Ana"
    assert fit("Anastasia", 5) == "Anas…"


def test_plural():
    assert [plural(1, "match"), plural(2, "match"), plural(3, "player")] == [
        "1 match",
        "2 matches",
        "3 players",
    ]


@pytest.mark.parametrize(
    ("result", "text"),
    [
        (None, "vs"),
        (Result.played(2, 1), "2 - 1"),
        (Result.forfeit(1), "F - W"),
        (Result.forfeit(2), "W - F"),
    ],
)
def test_result_text(result, text):
    assert result_text(Match(1, 1, 2, result)) == text


def test_signed_game_differential():
    assert [signed(3), signed(-2), signed(0)] == ["+3", "-2", "0"]


def test_player_table_shows_number_name_rating_and_seed(league):
    league.seed_by_rating()
    lines = player_lines(league.tournament.players)
    assert lines[1].split() == ["1", "Ana", "1500", "2"]
    assert lines[3].split() == ["3", "Cleo", "3"]


def test_round_table_shows_results_byes_and_the_forfeit_key(league):
    league.seed_by_rating()
    league.start()
    round_ = league.tournament.rounds[0]
    match = round_.matches[0]
    league.record_forfeit(match.id, match.player_a)
    text = "\n".join(round_lines(league.tournament, round_))
    assert "F - W" in text
    assert "Bye: " in text
    assert "F forfeited, W won by forfeit" in text


def test_us_09_6_standings_show_played_wins_draws_losses_and_points(league):
    league.seed_by_rating()
    league.start()
    match = league.tournament.rounds[0].matches[0]
    league.record_score(match.id, 1, 1)
    lines = standings_lines(league.tournament)
    assert lines[0].split() == ["Rank", "Name", "P", "W", "D", "L", "Pts", "GD"]
    drawn = [line.split() for line in lines[1:3]]
    assert all(row[2:] == ["1", "0", "1", "0", "1", "0"] for row in drawn)
    assert lines[-1].startswith("P played")


def full_session(format_key, count):
    """A started tournament with count players, each with a 40-character name."""
    session = TournamentSession()
    session.new("N" * 40, format_key)
    for number in range(1, count + 1):
        session.add_player(f"Player {number:02d} ".ljust(40, "x"), 999_999)
    session.seed_by_rating()
    session.start()
    return session


# 33 players in single elimination gives 31 byes, a long "Bye:" line.
@pytest.mark.parametrize(
    ("format_key", "count"), [("round_robin", 64), ("single_elimination", 33)]
)
def test_nfr_us_3_every_table_fits_80_columns_with_long_names(format_key, count):
    session = full_session(format_key, count)
    tournament = session.tournament
    first = tournament.rounds[0]
    for match in first.matches:
        session.record_score(match.id, 10, 12)
    session.path = Path("x" * 100 + ".bracketeer")
    lines = (
        player_lines(tournament.players)
        + round_lines(tournament, first)
        + standings_lines(tournament)
        + status_lines(session)
    )
    too_wide = [line for line in lines if len(line) > 80]
    assert not too_wide, too_wide[0]
