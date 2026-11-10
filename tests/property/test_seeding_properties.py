"""Property-based tests for seeding (R-SD-1, R-SD-2)."""

from itertools import pairwise

from hypothesis import given
from hypothesis import strategies as st

from bracketeer.domain.formats.round_robin import RoundRobin
from bracketeer.domain.tournament import MAX_PLAYERS, Tournament

# A rating is either missing or a whole number of 0 or more.
ratings = st.none() | st.integers(min_value=0, max_value=3000)
rating_lists = st.lists(ratings, max_size=MAX_PLAYERS)


def make_tournament(player_ratings):
    """Build a tournament with one player per rating, in that order."""
    tournament = Tournament("Generated", RoundRobin())
    for number, rating in enumerate(player_ratings):
        tournament.add_player(f"Player {number}", rating)
    return tournament


def seeds_are_1_to_n(tournament):
    seeds = sorted(player.seed for player in tournament.players)
    return seeds == list(range(1, len(tournament.players) + 1))


def ranks_before(a, b):
    """R-SD-2, written out: should player a get a better seed than player b?"""
    if a.rating is not None and b.rating is None:
        return True
    if a.rating is None and b.rating is not None:
        return False
    if a.rating != b.rating:
        return a.rating > b.rating
    return a.id < b.id


@given(rating_lists, st.randoms())
def test_random_seeding_gives_seeds_1_to_n(player_ratings, rng):
    tournament = make_tournament(player_ratings)
    tournament.seed_randomly(rng)
    assert seeds_are_1_to_n(tournament)


@given(rating_lists)
def test_seeding_by_rating_orders_every_neighbouring_pair(player_ratings):
    tournament = make_tournament(player_ratings)
    tournament.seed_by_rating()
    assert seeds_are_1_to_n(tournament)
    in_seed_order = sorted(tournament.players, key=lambda p: p.seed)
    for better, worse in pairwise(in_seed_order):
        assert ranks_before(better, worse)


@given(st.data())
def test_manual_seeding_follows_any_order(data):
    tournament = make_tournament(data.draw(rating_lists))
    ids = [player.id for player in tournament.players]
    order = data.draw(st.permutations(ids))
    tournament.seed_manually(order)
    for seed, player_id in enumerate(order, start=1):
        assert tournament.player(player_id).seed == seed


@given(st.data())
def test_removing_a_seeded_player_keeps_seeds_1_to_n(data):
    player_ratings = data.draw(st.lists(ratings, min_size=1, max_size=MAX_PLAYERS))
    tournament = make_tournament(player_ratings)
    tournament.seed_by_rating()
    victim = data.draw(st.sampled_from([player.id for player in tournament.players]))
    tournament.remove_player(victim)
    assert seeds_are_1_to_n(tournament)
