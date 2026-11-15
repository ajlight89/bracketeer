"""Unit tests for recording and clearing results (US-07, R-RS-1 to R-RS-5)."""

import pytest

from bracketeer.domain.errors import (
    InvalidResultError,
    NotInMatchError,
    UnknownMatchError,
)
from bracketeer.domain.formats.single_elimination import SingleElimination
from bracketeer.domain.rounds import DRAW_POINTS, LOSS_POINTS, WIN_POINTS
from bracketeer.domain.tournament import Tournament
from bracketeer.domain.values import Result, ResultKind


def start_with(tournament, *names):
    """Register the players, seed them in that order, start, and return IDs."""
    ids = [tournament.add_player(name) for name in names]
    tournament.seed_manually(ids)
    tournament.start()
    return ids


@pytest.fixture
def ana_vs_ben(tournament):
    """A started round robin with one match: Ana (player A) against Ben."""
    ana, ben = start_with(tournament, "Ana", "Ben")
    match = tournament.rounds[0].matches[0]
    assert (match.player_a, match.player_b) == (ana, ben)
    return tournament, match, ana, ben


@pytest.fixture
def no_draw_match():
    """Ana against Ben in a started single elimination, which bans draws."""
    tournament = Tournament("Cup Night", SingleElimination())
    ana, ben = start_with(tournament, "Ana", "Ben")
    return tournament, tournament.rounds[0].matches[0], ana, ben


def test_match_finds_every_match_by_id(tournament):
    start_with(tournament, "Ana", "Ben", "Cal", "Dee")
    for played_round in tournament.rounds:
        for match in played_round.matches:
            assert tournament.match(match.id) is match


def test_an_unknown_match_id_is_rejected(ana_vs_ben):
    tournament, _, _, _ = ana_vs_ben
    with pytest.raises(UnknownMatchError):
        tournament.record_result(99, Result.played(2, 1))
    with pytest.raises(UnknownMatchError):
        tournament.clear_result(99)


def test_results_cannot_be_recorded_before_the_start(tournament):
    tournament.add_player("Ana")
    tournament.add_player("Ben")
    with pytest.raises(UnknownMatchError):
        tournament.record_result(1, Result.played(2, 1))


def test_a_win_gives_3_points_to_the_winner_and_0_to_the_loser(ana_vs_ben):
    # US-07 #1
    tournament, match, ana, ben = ana_vs_ben
    tournament.record_result(match.id, Result.played(2, 1))
    assert match.result == Result.played(2, 1)
    assert match.winner() == ana
    assert match.match_points_for(ana) == WIN_POINTS
    assert match.match_points_for(ben) == LOSS_POINTS


def test_equal_scores_are_a_draw_in_round_robin(ana_vs_ben):
    # US-07 #2
    tournament, match, ana, ben = ana_vs_ben
    tournament.record_result(match.id, Result.played(1, 1))
    assert match.result.is_draw()
    assert match.match_points_for(ana) == DRAW_POINTS
    assert match.match_points_for(ben) == DRAW_POINTS


def test_a_format_that_needs_a_winner_rejects_a_draw(no_draw_match):
    # US-07 #3
    tournament, match, _, _ = no_draw_match
    with pytest.raises(InvalidResultError, match="winner"):
        tournament.record_result(match.id, Result.played(2, 2))
    assert match.result is None


def test_a_format_that_needs_a_winner_accepts_wins_and_forfeits(no_draw_match):
    # R-RS-2, R-RS-5
    tournament, match, ana, ben = no_draw_match
    tournament.record_result(match.id, Result.played(3, 0))
    assert match.winner() == ana
    tournament.record_result(match.id, Result.forfeit(ana))
    assert match.winner() == ben


@pytest.mark.parametrize(
    ("score_a", "score_b"),
    [(-1, 2), (2, -1), ("2", 1), (1.5, 0)],
    ids=["negative a", "negative b", "string", "float"],
)
def test_negative_or_non_numeric_scores_are_rejected(ana_vs_ben, score_a, score_b):
    # US-07 #4
    tournament, match, _, _ = ana_vs_ben
    with pytest.raises(InvalidResultError):
        tournament.record_result(match.id, Result.played(score_a, score_b))
    assert match.result is None


def test_a_forfeit_is_a_win_for_the_opponent_with_no_game_score(ana_vs_ben):
    # US-07 #6
    tournament, match, ana, ben = ana_vs_ben
    tournament.record_result(match.id, Result.forfeit(ben))
    assert match.result.kind is ResultKind.FORFEIT
    assert (match.result.score_a, match.result.score_b) == (None, None)
    assert match.winner() == ana
    assert match.match_points_for(ana) == WIN_POINTS
    assert match.match_points_for(ben) == LOSS_POINTS


def test_only_a_player_in_the_match_can_forfeit_it(tournament):
    # R-RS-5
    ana, _, _ = start_with(tournament, "Ana", "Ben", "Cal")
    match = tournament.rounds[0].matches[0]
    assert not match.has_player(ana)  # Ana has the round 1 bye.
    with pytest.raises(NotInMatchError):
        tournament.record_result(match.id, Result.forfeit(ana))
    assert match.result is None


def test_a_new_result_replaces_the_old_one_in_round_robin(ana_vs_ben):
    # R-RS-7: round robin results can change at any time.
    tournament, match, _, ben = ana_vs_ben
    tournament.record_result(match.id, Result.played(2, 1))
    tournament.record_result(match.id, Result.played(0, 2))
    assert match.winner() == ben


def test_a_rejected_result_leaves_the_earlier_one_in_place(no_draw_match):
    tournament, match, _, _ = no_draw_match
    tournament.record_result(match.id, Result.played(2, 1))
    with pytest.raises(InvalidResultError):
        tournament.record_result(match.id, Result.played(1, 1))
    assert match.result == Result.played(2, 1)


def test_clearing_a_result_makes_the_match_unplayed_again(ana_vs_ben):
    # US-07 #7
    tournament, match, ana, ben = ana_vs_ben
    tournament.record_result(match.id, Result.played(2, 1))
    tournament.clear_result(match.id)
    assert match.result is None
    assert match.match_points_for(ana) == 0
    assert match.match_points_for(ben) == 0
    assert not tournament.rounds[0].is_finished()


def test_clearing_an_unplayed_match_changes_nothing(ana_vs_ben):
    tournament, match, _, _ = ana_vs_ben
    tournament.clear_result(match.id)
    assert match.result is None
