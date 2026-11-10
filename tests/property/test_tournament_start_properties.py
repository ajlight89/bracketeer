"""Property-based tests for starting a tournament (R-RR-1)."""

from hypothesis import given
from hypothesis import strategies as st

from bracketeer.domain.formats.round_robin import RoundRobin
from bracketeer.domain.tournament import MAX_PLAYERS, MIN_PLAYERS, Tournament


@given(st.integers(MIN_PLAYERS, MAX_PLAYERS), st.randoms(use_true_random=False))
def test_starting_numbers_every_match_once(count, rng):
    tournament = Tournament("Generated", RoundRobin())
    for number in range(count):
        tournament.add_player(f"Player {number}")
    tournament.seed_randomly(rng)
    tournament.start()
    matches = [match for round_ in tournament.rounds for match in round_.matches]
    assert len(matches) == count * (count - 1) // 2
    assert [match.id for match in matches] == list(range(1, len(matches) + 1))
    registered = {player.id for player in tournament.players}
    assert all({match.player_a, match.player_b} <= registered for match in matches)
