"""Unit tests for the round robin format (R-RR, US-05)."""

import dataclasses
import inspect

import pytest

from bracketeer.domain.formats.base import RoundPlan, TournamentFormat
from bracketeer.domain.formats.round_robin import RoundRobin


def schedule(player_count):
    return RoundRobin().first_rounds(range(1, player_count + 1))


def test_the_format_interface_cannot_be_used_directly():
    with pytest.raises(TypeError):
        TournamentFormat()


def test_round_robin_settings():
    assert RoundRobin.key == "round_robin"
    assert RoundRobin.allows_draws
    assert not RoundRobin.locks_results


def test_round_robin_sets_every_setting_the_interface_declares():
    for name in inspect.get_annotations(TournamentFormat):
        assert hasattr(RoundRobin, name), name


def test_six_players_play_five_rounds_of_three_matches():
    plans = schedule(6)
    assert len(plans) == 5
    assert all(len(plan.pairings) == 3 for plan in plans)
    assert all(plan.byes == () for plan in plans)


def test_first_round_pairs_top_seeds_with_bottom_seeds():
    assert schedule(6)[0].pairings == ((1, 6), (2, 5), (3, 4))


def test_seven_players_play_seven_rounds_with_one_bye_each():
    plans = schedule(7)
    assert len(plans) == 7
    assert sum(len(plan.pairings) for plan in plans) == 21
    assert all(len(plan.byes) == 1 for plan in plans)
    assert sorted(plan.byes[0] for plan in plans) == list(range(1, 8))


def test_the_whole_schedule_is_planned_at_the_start(tournament):
    assert RoundRobin().next_round(tournament) is None


def test_a_round_plan_cannot_be_changed():
    plan = RoundPlan(((1, 2),))
    assert plan.byes == ()
    with pytest.raises(dataclasses.FrozenInstanceError):
        plan.byes = (3,)
