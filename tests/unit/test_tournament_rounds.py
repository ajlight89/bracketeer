"""Unit tests for later rounds, locked results, and completion (R-RD, R-RS-7)."""

import pytest

from bracketeer.domain.errors import (
    NoNextRoundError,
    ResultLockedError,
    RoundNotFinishedError,
)
from bracketeer.domain.formats.single_elimination import SingleElimination
from bracketeer.domain.tournament import Tournament
from bracketeer.domain.values import Result


def start(tournament, player_count):
    """Add players 1 to player_count, seed them in that order, and start."""
    ids = [tournament.add_player(f"Player {n}") for n in range(1, player_count + 1)]
    tournament.seed_manually(ids)
    tournament.start()
    return tournament


def start_bracket(player_count):
    """Start a single elimination tournament whose player IDs are their seeds."""
    return start(Tournament("Cup Night", SingleElimination()), player_count)


def finish_last_round(tournament, winners):
    """Record a result in every match of the last round; listed players win."""
    for match in tournament.rounds[-1].matches:
        if match.player_a in winners:
            result = Result.played(2, 1)
        else:
            result = Result.played(1, 2)
        tournament.record_result(match.id, result)


def top_seeds_win(tournament):
    """Finish the last round with the higher seed (player A) winning each match."""
    finish_last_round(tournament, {m.player_a for m in tournament.rounds[-1].matches})


def test_generate_next_round_pairs_the_winners():
    # R-SE-3
    tournament = start_bracket(8)
    finish_last_round(tournament, winners={1, 5, 2, 6})
    tournament.generate_next_round()
    second = tournament.rounds[1]
    assert second.number == 2
    assert [(m.player_a, m.player_b) for m in second.matches] == [(1, 5), (2, 6)]


def test_match_numbers_continue_in_the_next_round():
    tournament = start_bracket(8)
    top_seeds_win(tournament)
    tournament.generate_next_round()
    assert [m.id for m in tournament.rounds[1].matches] == [5, 6]


def test_the_next_round_needs_a_result_in_every_match():
    # R-RD-1
    tournament = start_bracket(4)
    first_match = tournament.rounds[0].matches[0]
    tournament.record_result(first_match.id, Result.played(2, 0))
    with pytest.raises(RoundNotFinishedError):
        tournament.generate_next_round()
    assert len(tournament.rounds) == 1


def test_no_round_can_be_generated_before_the_start():
    tournament = Tournament("Cup Night", SingleElimination())
    with pytest.raises(NoNextRoundError):
        tournament.generate_next_round()


def test_no_round_follows_the_final():
    tournament = start_bracket(2)
    top_seeds_win(tournament)
    with pytest.raises(NoNextRoundError):
        tournament.generate_next_round()


def test_round_robin_never_generates_a_round(tournament):
    # R-RR-3: the whole schedule is planned at the start.
    start(tournament, 2)
    top_seeds_win(tournament)
    with pytest.raises(NoNextRoundError):
        tournament.generate_next_round()


def test_a_whole_bracket_has_n_minus_1_matches_and_one_champion():
    # R-SE-3, R-SE-4
    tournament = start_bracket(6)
    top_seeds_win(tournament)
    while not tournament.is_complete():
        tournament.generate_next_round()
        top_seeds_win(tournament)
    assert len(tournament.rounds) == 3
    assert sum(len(r.matches) for r in tournament.rounds) == 5
    ranks = [s.rank for s in tournament.standings()]
    assert ranks.count(1) == 1
    assert tournament.standings()[0].player_id == 1


def test_results_can_change_until_the_next_round_exists():
    # R-RS-7
    tournament = start_bracket(4)
    match = tournament.rounds[0].matches[0]
    tournament.record_result(match.id, Result.played(2, 1))
    tournament.record_result(match.id, Result.played(0, 2))
    assert match.result == Result.played(0, 2)


def test_a_result_is_locked_once_the_next_round_exists():
    # US-07 #5
    tournament = start_bracket(4)
    top_seeds_win(tournament)
    tournament.generate_next_round()
    match = tournament.rounds[0].matches[0]
    with pytest.raises(ResultLockedError, match="next round"):
        tournament.record_result(match.id, Result.played(0, 2))
    assert match.result == Result.played(2, 1)


def test_a_locked_result_cannot_be_cleared():
    # R-RS-7
    tournament = start_bracket(4)
    top_seeds_win(tournament)
    tournament.generate_next_round()
    match = tournament.rounds[0].matches[0]
    with pytest.raises(ResultLockedError):
        tournament.clear_result(match.id)
    assert match.result == Result.played(2, 1)


def test_results_in_the_current_round_can_still_change():
    # R-RS-7
    tournament = start_bracket(4)
    top_seeds_win(tournament)
    tournament.generate_next_round()
    final = tournament.rounds[1].matches[0]
    tournament.record_result(final.id, Result.played(2, 1))
    tournament.clear_result(final.id)
    assert final.result is None


def test_round_robin_results_never_lock(tournament):
    # R-RS-7: every round exists from the start, and round 1 can still change.
    start(tournament, 4)
    match = tournament.rounds[0].matches[0]
    tournament.record_result(match.id, Result.played(2, 1))
    tournament.record_result(match.id, Result.played(1, 1))
    assert match.result.is_draw()


def test_a_tournament_is_not_complete_before_it_starts(tournament):
    assert not tournament.is_complete()


def test_round_robin_is_complete_once_every_result_is_in(tournament):
    # R-RD-4
    start(tournament, 3)
    matches = [m for r in tournament.rounds for m in r.matches]
    for match in matches[:-1]:
        tournament.record_result(match.id, Result.played(2, 1))
    assert not tournament.is_complete()
    tournament.record_result(matches[-1].id, Result.played(2, 1))
    assert tournament.is_complete()


def test_single_elimination_is_complete_after_the_final():
    # R-RD-4
    tournament = start_bracket(2)
    assert not tournament.is_complete()
    top_seeds_win(tournament)
    assert tournament.is_complete()
