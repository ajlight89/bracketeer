"""Unit tests for starting a tournament (US-02 #3 and #4, US-03 #5, US-05)."""

from random import Random

import pytest

from bracketeer.domain.errors import (
    DuplicateNameError,
    InvalidSeedingError,
    PlayerCountError,
    TournamentStartedError,
)
from bracketeer.domain.formats.round_robin import RoundRobin


def ready(tournament, count):
    """Register count players and seed them in registration order."""
    ids = [tournament.add_player(f"Player {n}") for n in range(1, count + 1)]
    tournament.seed_manually(ids)
    return ids


def snapshot(tournament):
    return [(p.id, p.name.text, p.rating, p.seed) for p in tournament.players]


def test_new_tournament_has_not_started(tournament):
    assert not tournament.started
    assert tournament.rounds == ()
    assert isinstance(tournament.format, RoundRobin)


def test_starting_a_round_robin_plans_every_round(tournament):
    ready(tournament, 6)
    tournament.start()
    assert tournament.started
    assert [r.number for r in tournament.rounds] == [1, 2, 3, 4, 5]
    assert all(len(r.matches) == 3 for r in tournament.rounds)


def test_matches_are_numbered_from_1_across_rounds(tournament):
    ready(tournament, 6)
    tournament.start()
    match_ids = [m.id for r in tournament.rounds for m in r.matches]
    assert match_ids == list(range(1, 16))


def test_the_format_gets_the_players_in_seed_order(tournament):
    ids = ready(tournament, 4)
    tournament.seed_manually(list(reversed(ids)))
    tournament.start()
    first = tournament.rounds[0].matches[0]
    assert (first.player_a, first.player_b) == (ids[3], ids[0])


def test_byes_are_copied_into_the_rounds(tournament):
    ids = ready(tournament, 3)
    tournament.start()
    assert tournament.rounds[0].byes == [ids[0]]


@pytest.mark.parametrize("count", [0, 1])
def test_fewer_than_two_players_cannot_start(tournament, count):
    ready(tournament, count)
    with pytest.raises(PlayerCountError):
        tournament.start()
    assert not tournament.started


def test_unseeded_players_cannot_start(tournament):
    tournament.add_player("Ana")
    tournament.add_player("Ben")
    with pytest.raises(InvalidSeedingError):
        tournament.start()
    assert tournament.rounds == ()


def test_a_tournament_cannot_start_twice(tournament):
    ready(tournament, 2)
    tournament.start()
    with pytest.raises(TournamentStartedError):
        tournament.start()


@pytest.mark.parametrize(
    "action",
    [
        lambda t: t.add_player("Late"),
        lambda t: t.edit_player(1, "Ana", None),
        lambda t: t.remove_player(1),
        lambda t: t.seed_manually([2, 1]),
        lambda t: t.seed_randomly(Random(1)),
        lambda t: t.seed_by_rating(),
    ],
    ids=["add", "edit", "remove", "seed manually", "seed randomly", "seed by rating"],
)
def test_players_and_seeds_are_fixed_after_the_start(tournament, action):
    ready(tournament, 2)
    tournament.start()
    before = snapshot(tournament)
    with pytest.raises(TournamentStartedError):
        action(tournament)
    assert snapshot(tournament) == before


def test_a_name_can_be_corrected_after_the_start(tournament):
    ids = ready(tournament, 2)
    tournament.start()
    tournament.rename_player(ids[0], "  Ana  ")
    assert tournament.player(ids[0]).name.text == "Ana"


def test_a_corrected_name_must_still_be_free(tournament):
    ids = ready(tournament, 2)
    tournament.start()
    with pytest.raises(DuplicateNameError):
        tournament.rename_player(ids[0], "player 2")
