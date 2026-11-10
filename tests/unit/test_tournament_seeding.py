"""Unit tests for seeding players (US-03, US-02 #2)."""

import random

import pytest

from bracketeer.domain.errors import InvalidSeedingError
from bracketeer.domain.formats.round_robin import RoundRobin
from bracketeer.domain.tournament import Tournament


def seeds(tournament):
    """Map each player's name to their seed."""
    return {player.name.text: player.seed for player in tournament.players}


def test_players_are_unseeded_until_seeded(tournament):
    tournament.add_player("Ana")
    assert seeds(tournament) == {"Ana": None}


def test_random_seeding_gives_unique_seeds_1_to_n(tournament):  # US-03 #1
    for name in "ABCDEFGH":
        tournament.add_player(name)
    tournament.seed_randomly(random.Random(42))
    assert sorted(seeds(tournament).values()) == list(range(1, 9))


def test_random_seeding_is_repeatable_with_the_same_generator_seed():
    results = []
    for _ in range(2):
        tournament = Tournament("Repeat", RoundRobin())
        for name in "ABCDEFGH":
            tournament.add_player(name)
        tournament.seed_randomly(random.Random(7))
        results.append(seeds(tournament))
    assert results[0] == results[1]


def test_seeding_by_rating_puts_the_highest_first(tournament):  # US-03 #2
    tournament.add_player("Ana", 1500)
    tournament.add_player("Ben", 1800)
    tournament.add_player("Cara", 1200)
    tournament.seed_by_rating()
    assert seeds(tournament) == {"Ana": 2, "Ben": 1, "Cara": 3}


def test_unrated_players_come_last_in_registration_order(tournament):  # US-03 #3
    tournament.add_player("Ana")
    tournament.add_player("Ben", 1200)
    tournament.add_player("Cara")
    tournament.add_player("Dev", 1500)
    tournament.seed_by_rating()
    assert seeds(tournament) == {"Dev": 1, "Ben": 2, "Ana": 3, "Cara": 4}


def test_equal_ratings_keep_registration_order(tournament):
    tournament.add_player("Ana", 1500)
    tournament.add_player("Ben", 1500)
    tournament.seed_by_rating()
    assert seeds(tournament) == {"Ana": 1, "Ben": 2}


def test_a_rating_of_zero_still_counts_as_rated(tournament):
    tournament.add_player("Ana")
    tournament.add_player("Ben", 0)
    tournament.seed_by_rating()
    assert seeds(tournament) == {"Ben": 1, "Ana": 2}


def test_manual_seeding_follows_the_given_order(tournament):  # US-03 #4
    ana = tournament.add_player("Ana")
    ben = tournament.add_player("Ben")
    cara = tournament.add_player("Cara")
    tournament.seed_manually([cara, ana, ben])
    assert seeds(tournament) == {"Cara": 1, "Ana": 2, "Ben": 3}


@pytest.mark.parametrize(
    "order",
    [[1, 2], [1, 2, 2], [1, 2, 3, 4], [1, 2, 99]],
    ids=["missing", "duplicate", "extra", "unknown"],
)
def test_manual_seeding_must_list_every_player_once(tournament, order):
    for name in ["Ana", "Ben", "Cara"]:
        tournament.add_player(name)
    with pytest.raises(InvalidSeedingError):
        tournament.seed_manually(order)
    assert set(seeds(tournament).values()) == {None}


def test_removing_a_seeded_player_renumbers_the_rest(tournament):  # US-02 #2
    ana = tournament.add_player("Ana")
    ben = tournament.add_player("Ben")
    cara = tournament.add_player("Cara")
    tournament.seed_manually([cara, ana, ben])
    tournament.remove_player(ana)
    assert seeds(tournament) == {"Cara": 1, "Ben": 2}


def test_a_player_added_after_seeding_gets_the_next_seed(tournament):
    ana = tournament.add_player("Ana")
    ben = tournament.add_player("Ben")
    tournament.seed_manually([ben, ana])
    tournament.add_player("Cara")
    assert seeds(tournament) == {"Ben": 1, "Ana": 2, "Cara": 3}
