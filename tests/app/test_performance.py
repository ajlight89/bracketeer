"""NFR-PE-1: with 64 players, every action responds within 1 second.

Each test times one action on a 64-player tournament, the most allowed
(R-PL-1). The actions take a few milliseconds, so the limit leaves plenty of
room on slower computers, such as the GitHub Actions runners.
"""

import time
from random import Random

import pytest

from bracketeer.app.session import TournamentSession

LIMIT = 1.0  # seconds


def seeded_64_players(format_key: str) -> TournamentSession:
    rng = Random(345)
    session = TournamentSession(rng=rng)
    session.new("64-Player Test", format_key)
    for number in range(1, 65):
        session.add_player(f"Player {number:02d}", rng.randint(1000, 2400))
    session.seed_by_rating()
    return session


def seconds(action) -> float:
    start = time.perf_counter()
    action()
    return time.perf_counter() - start


@pytest.fixture
def league():
    """A 64-player round robin with 32 of its 63 rounds played."""
    session = seeded_64_players("round_robin")
    session.start()
    for round_ in session.tournament.rounds[:32]:
        for match in round_.matches:
            session.record_score(match.id, 2, 1)
    return session


def test_nfr_pe_1_starting_a_64_player_round_robin():
    # Round robin plans all 63 rounds at the start: the slowest start.
    session = seeded_64_players("round_robin")
    assert seconds(session.start) < LIMIT


def test_nfr_pe_1_entering_a_result(league):
    match = league.tournament.rounds[32].matches[0]
    assert seconds(lambda: league.record_score(match.id, 2, 1)) < LIMIT


def test_nfr_pe_1_refreshing_the_standings(league):
    assert seconds(league.tournament.standings) < LIMIT


def test_nfr_pe_1_generating_the_next_round():
    session = seeded_64_players("single_elimination")
    session.start()
    for match in session.tournament.rounds[0].matches:
        session.record_score(match.id, 2, 0)
    assert seconds(session.generate_next_round) < LIMIT
