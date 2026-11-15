"""Unit tests for the single elimination format (R-SE, US-05)."""

import inspect

import pytest

from bracketeer.domain.formats.base import TournamentFormat
from bracketeer.domain.formats.single_elimination import SingleElimination
from bracketeer.domain.tournament import Tournament
from bracketeer.domain.values import Result


def first_round(player_count):
    """Plan round 1 for players 1 to player_count, where player n is seed n."""
    return SingleElimination().first_rounds(range(1, player_count + 1))[0]


def start_bracket(player_count):
    """Start a tournament whose player IDs are also their seeds."""
    tournament = Tournament("Cup Night", SingleElimination())
    ids = [tournament.add_player(f"Player {n}") for n in range(1, player_count + 1)]
    tournament.seed_manually(ids)
    tournament.start()
    return tournament


def finish_last_round(tournament, winners):
    """Record a result in every match of the last round; listed players win."""
    for match in tournament.rounds[-1].matches:
        if match.player_a in winners:
            result = Result.played(2, 1)
        else:
            result = Result.played(1, 2)
        tournament.record_result(match.id, result)


def test_single_elimination_settings():
    assert SingleElimination.key == "single_elimination"
    assert not SingleElimination.allows_draws
    assert SingleElimination.locks_results


def test_single_elimination_sets_every_setting_the_interface_declares():
    for name in inspect.get_annotations(TournamentFormat):
        assert hasattr(SingleElimination, name), name


def test_only_round_1_is_planned_at_the_start():
    plans = SingleElimination().first_rounds(range(1, 9))
    assert len(plans) == 1


def test_eight_players_follow_the_standard_bracket_order():
    # R-SE-2
    plan = first_round(8)
    assert plan.pairings == ((1, 8), (4, 5), (2, 7), (3, 6))
    assert plan.byes == ()


def test_six_players_give_byes_to_the_top_two_seeds():
    # R-SE-1
    plan = first_round(6)
    assert plan.byes == (1, 2)
    assert plan.pairings == ((4, 5), (3, 6))


def test_two_players_meet_in_one_match():
    plan = first_round(2)
    assert plan.pairings == ((1, 2),)
    assert plan.byes == ()


@pytest.mark.parametrize(
    ("player_count", "bracket_size"),
    [(2, 2), (3, 4), (5, 8), (8, 8), (9, 16), (64, 64)],
)
def test_the_bracket_fills_the_next_power_of_2_with_byes(player_count, bracket_size):
    # R-SE-1
    plan = first_round(player_count)
    # Every pair, a match or a bye, fills two slots of the bracket.
    assert 2 * (len(plan.pairings) + len(plan.byes)) == bracket_size
    assert len(plan.byes) == bracket_size - player_count


def test_players_are_placed_by_seed_not_by_id():
    # R-SE-1: the IDs are given in seed order, so ID 30 is seed 1
    plan = SingleElimination().first_rounds([30, 10, 20])[0]
    assert plan.byes == (30,)
    assert plan.pairings == ((10, 20),)


def test_round_2_pairs_the_round_1_winners_in_bracket_order():
    # R-SE-3: seeds 5 and 6 win their matches
    tournament = start_bracket(8)
    finish_last_round(tournament, winners={1, 5, 2, 6})
    plan = SingleElimination().next_round(tournament)
    assert plan.pairings == ((1, 5), (2, 6))
    assert plan.byes == ()


def test_players_with_a_bye_join_round_2_in_their_bracket_slot():
    # R-SE-1: seeds 1 and 2 have byes; seeds 5 and 3 win their matches
    tournament = start_bracket(6)
    finish_last_round(tournament, winners={5, 3})
    plan = SingleElimination().next_round(tournament)
    assert plan.pairings == ((1, 5), (2, 3))


def test_no_round_follows_the_final():
    tournament = start_bracket(2)
    finish_last_round(tournament, winners={2})
    assert SingleElimination().next_round(tournament) is None


def test_tournament_standings_use_placement_order():
    # US-09 #5: the format decides the order, so the winner is listed first
    tournament = start_bracket(2)
    finish_last_round(tournament, winners={2})
    assert [s.player_id for s in tournament.standings()] == [2, 1]
