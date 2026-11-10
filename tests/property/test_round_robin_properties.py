"""Property-based tests for the round robin schedule (R-RR-1, R-RR-2, R-RD-2)."""

from itertools import combinations

from hypothesis import given
from hypothesis import strategies as st

from bracketeer.domain.formats.round_robin import RoundRobin

# Player IDs in seed order. IDs can have gaps (players removed before the
# start) and don't need to be in ID order, so any distinct numbers will do.
seeded_ids = st.lists(st.integers(1, 1_000), min_size=2, max_size=64, unique=True)


@given(seeded_ids)
def test_every_pair_meets_exactly_once(ids):
    plans = RoundRobin().first_rounds(ids)
    pairs = [frozenset(pair) for plan in plans for pair in plan.pairings]
    expected = {frozenset(pair) for pair in combinations(ids, 2)}
    assert len(pairs) == len(expected)
    assert set(pairs) == expected


@given(seeded_ids)
def test_rounds_and_byes_depend_on_the_player_count(ids):
    plans = RoundRobin().first_rounds(ids)
    if len(ids) % 2 == 0:
        assert len(plans) == len(ids) - 1
        assert all(plan.byes == () for plan in plans)
    else:
        assert len(plans) == len(ids)
        assert all(len(plan.byes) == 1 for plan in plans)
        assert sorted(plan.byes[0] for plan in plans) == sorted(ids)


@given(seeded_ids)
def test_every_player_appears_exactly_once_in_every_round(ids):
    for plan in RoundRobin().first_rounds(ids):
        players = [player for pair in plan.pairings for player in pair]
        players += plan.byes
        assert sorted(players) == sorted(ids)
