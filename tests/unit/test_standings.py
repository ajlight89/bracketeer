"""Unit tests for round robin standings (US-09, R-TB-1 to R-TB-3)."""

import dataclasses

import pytest

from bracketeer.domain.standings import Standing
from bracketeer.domain.values import Result


def start_with(tournament, *names):
    """Register the players, seed them in that order, start, and return IDs."""
    ids = [tournament.add_player(name) for name in names]
    tournament.seed_manually(ids)
    tournament.start()
    return ids


def match_between(tournament, first, second):
    """Return the match between two players, whichever of them is player A."""
    for played_round in tournament.rounds:
        for match in played_round.matches:
            if match.has_player(first) and match.has_player(second):
                return match
    raise AssertionError(f"Players {first} and {second} never meet.")


def play(tournament, first, second, first_score, second_score):
    """Record a played result, with the scores given in the order of the IDs."""
    match = match_between(tournament, first, second)
    if match.player_a == first:
        result = Result.played(first_score, second_score)
    else:
        result = Result.played(second_score, first_score)
    tournament.record_result(match.id, result)
    return match


def row_for(tournament, player_id):
    """Return the player's row in the current standings."""
    rows = [s for s in tournament.standings() if s.player_id == player_id]
    assert len(rows) == 1
    return rows[0]


def ranked_ids(tournament):
    return [standing.player_id for standing in tournament.standings()]


def test_played_counts_wins_draws_and_losses():
    standing = Standing(1, 1, 7, 2, 1, 3, 0)
    assert standing.played() == 6


def test_a_standing_cannot_be_changed():
    standing = Standing(1, 1, 3, 1, 0, 0, 2)
    with pytest.raises(dataclasses.FrozenInstanceError):
        standing.rank = 2


def test_standings_list_every_player_once_before_the_start(tournament):
    # US-09 #2
    ids = [tournament.add_player(name) for name in ("Ana", "Ben", "Cal")]
    assert sorted(ranked_ids(tournament)) == sorted(ids)


def test_standings_list_every_player_once_after_results(tournament):
    # US-09 #2
    ids = start_with(tournament, "Ana", "Ben", "Cal", "Dee", "Eve")
    play(tournament, ids[0], ids[1], 2, 0)
    play(tournament, ids[2], ids[3], 1, 1)
    assert sorted(ranked_ids(tournament)) == sorted(ids)


def test_ranks_run_from_1_with_no_gaps(tournament):
    start_with(tournament, "Ana", "Ben", "Cal", "Dee")
    ranks = [standing.rank for standing in tournament.standings()]
    assert ranks == [1, 2, 3, 4]


def test_a_win_and_a_loss_are_counted(tournament):
    # US-09 #6
    ana, ben = start_with(tournament, "Ana", "Ben")
    play(tournament, ana, ben, 3, 1)
    assert row_for(tournament, ana) == Standing(ana, 1, 3, 1, 0, 0, 2)
    assert row_for(tournament, ben) == Standing(ben, 2, 0, 0, 0, 1, -2)


def test_player_b_gets_the_game_differential_from_their_side(tournament):
    ana, ben = start_with(tournament, "Ana", "Ben")
    match = play(tournament, ben, ana, 2, 0)
    assert match.player_b == ben
    assert row_for(tournament, ben).game_differential == 2
    assert row_for(tournament, ana).game_differential == -2


def test_a_draw_gives_each_player_1_point(tournament):
    # US-09 #6
    ana, ben = start_with(tournament, "Ana", "Ben")
    play(tournament, ana, ben, 2, 2)
    for player_id in (ana, ben):
        standing = row_for(tournament, player_id)
        assert (standing.match_points, standing.draws) == (1, 1)
        assert standing.game_differential == 0


def test_a_forfeit_counts_as_a_win_and_a_loss_with_no_game_score(tournament):
    # R-RS-5, R-RS-6
    ana, ben = start_with(tournament, "Ana", "Ben")
    match = match_between(tournament, ana, ben)
    tournament.record_result(match.id, Result.forfeit(ben))
    assert row_for(tournament, ana) == Standing(ana, 1, 3, 1, 0, 0, 0)
    assert row_for(tournament, ben) == Standing(ben, 2, 0, 0, 0, 1, 0)


def test_a_bye_adds_nothing(tournament):
    # R-RS-4: with 3 players, someone sits out each round.
    start_with(tournament, "Ana", "Ben", "Cal")
    first_round = tournament.rounds[0]
    (bye,) = first_round.byes
    (match,) = first_round.matches
    tournament.record_result(match.id, Result.played(1, 0))
    standing = row_for(tournament, bye)
    assert (standing.played(), standing.match_points) == (0, 0)
    assert standing.game_differential == 0


def test_standings_update_when_a_result_is_cleared(tournament):
    # US-09 #1
    ana, ben = start_with(tournament, "Ana", "Ben")
    match = play(tournament, ana, ben, 0, 2)
    assert ranked_ids(tournament) == [ben, ana]
    tournament.clear_result(match.id)
    assert ranked_ids(tournament) == [ana, ben]
    assert row_for(tournament, ben).played() == 0


def test_match_points_rank_before_game_differential(tournament):
    # R-TB-2: Cal wins one match narrowly; Ben loses one heavily but draws one.
    ana, ben, cal = start_with(tournament, "Ana", "Ben", "Cal")
    play(tournament, ana, ben, 9, 0)
    play(tournament, cal, ana, 1, 0)
    play(tournament, ben, cal, 0, 0)
    # Cal 4 points (+1), Ana 3 points (+8), Ben 1 point (-9).
    assert ranked_ids(tournament) == [cal, ana, ben]


def test_game_differential_breaks_a_tie_on_match_points(tournament):
    # US-09 #3: Ana and Ben both have 4 points. Ben is seed 1, so only
    # Ana's higher game differential can put her first.
    ben, ana, cal = start_with(tournament, "Ben", "Ana", "Cal")
    play(tournament, ana, ben, 1, 1)
    play(tournament, ana, cal, 3, 0)
    play(tournament, ben, cal, 1, 0)
    assert ranked_ids(tournament) == [ana, ben, cal]


def test_seed_breaks_a_tie_on_everything_else(tournament):
    # US-09 #4, R-TB-3: no results yet, so everyone is tied on 0 and 0.
    ana, ben, cal = (tournament.add_player(n) for n in ("Ana", "Ben", "Cal"))
    tournament.seed_manually([cal, ana, ben])
    tournament.start()
    assert ranked_ids(tournament) == [cal, ana, ben]


def test_unseeded_players_are_listed_in_registration_order(tournament):
    ids = [tournament.add_player(name) for name in ("Ana", "Ben", "Cal")]
    assert ranked_ids(tournament) == ids
