"""Unit tests for the Round entity."""

from bracketeer.domain.rounds import Match, Round
from bracketeer.domain.values import Result


def make_round(*results):
    # Match n is between players 2n - 1 and 2n, so no player appears twice.
    matches = [
        Match(number, 2 * number - 1, 2 * number, result)
        for number, result in enumerate(results, start=1)
    ]
    return Round(1, matches)


def test_round_with_no_results_is_not_finished():
    assert not make_round(None, None).is_finished()


def test_round_with_some_results_is_not_finished():
    assert not make_round(Result.played(2, 1), None).is_finished()


def test_round_with_every_result_is_finished():
    assert make_round(Result.played(2, 1), Result.forfeit(3)).is_finished()


def test_byes_default_to_an_empty_list():
    assert make_round().byes == []


def test_rounds_do_not_share_their_byes_list():
    first = make_round()
    second = make_round()
    first.byes.append(7)
    assert second.byes == []
