"""Fixtures for the persistence tests: tournaments worth saving."""

import pytest

from bracketeer.domain.formats.round_robin import RoundRobin
from bracketeer.domain.formats.single_elimination import SingleElimination
from bracketeer.domain.tournament import Tournament
from bracketeer.domain.values import Result


@pytest.fixture
def league():
    """A 5-player round robin, partly played: wins, a draw, a forfeit, byes."""
    tournament = Tournament("Friday Smash Night", RoundRobin())
    ratings = {"Ana": 1500, "Ben": None, "Cleo": 1200, "Dev": 1350, "Eve": None}
    for name, rating in ratings.items():
        tournament.add_player(name, rating)
    tournament.seed_by_rating()
    tournament.start()
    first, second = tournament.rounds[0].matches, tournament.rounds[1].matches
    tournament.record_result(first[0].id, Result.played(2, 1))
    tournament.record_result(first[1].id, Result.forfeit(first[1].player_b))
    tournament.record_result(second[0].id, Result.played(1, 1))
    return tournament


@pytest.fixture
def bracket():
    """A 6-player single elimination in round 2: byes, an upset, a forfeit."""
    tournament = Tournament("Cup Night", SingleElimination())
    names = ["Ana", "Ben", "Cleo", "Dev", "Eve", "Finn"]
    ids = [tournament.add_player(name) for name in names]
    tournament.seed_manually(ids)
    tournament.start()
    first = tournament.rounds[0].matches
    tournament.record_result(first[0].id, Result.played(0, 2))
    tournament.record_result(first[1].id, Result.forfeit(first[1].player_a))
    tournament.generate_next_round()
    second = tournament.rounds[1].matches
    tournament.record_result(second[0].id, Result.played(3, 1))
    return tournament
