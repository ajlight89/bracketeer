"""Unit tests for the Match entity (R-RS-1, R-RS-3, R-RS-5)."""

import pytest

from bracketeer.domain.errors import NotInMatchError
from bracketeer.domain.rounds import Match
from bracketeer.domain.values import Result

ANA = 1
BO = 2


def make_match(result=None):
    return Match(1, ANA, BO, result)


def test_new_match_has_no_result_and_no_winner():
    match = make_match()
    assert match.result is None
    assert match.winner() is None


@pytest.mark.parametrize(
    ("result", "expected"),
    [
        (Result.played(2, 1), ANA),
        (Result.played(0, 3), BO),
        (Result.played(2, 2), None),
        (Result.forfeit(BO), ANA),
        (Result.forfeit(ANA), BO),
    ],
    ids=["a wins", "b wins", "draw", "b forfeits", "a forfeits"],
)
def test_winner(result, expected):
    assert make_match(result).winner() == expected


@pytest.mark.parametrize(
    ("result", "expected"),
    [
        (None, (0, 0)),
        (Result.played(2, 1), (3, 0)),
        (Result.played(1, 2), (0, 3)),
        (Result.played(2, 2), (1, 1)),
        (Result.forfeit(ANA), (0, 3)),
        (Result.forfeit(BO), (3, 0)),
    ],
    ids=["no result", "a wins", "b wins", "draw", "a forfeits", "b forfeits"],
)
def test_match_points(result, expected):
    match = make_match(result)
    assert (match.match_points_for(ANA), match.match_points_for(BO)) == expected


def test_has_player():
    match = make_match()
    assert match.has_player(ANA)
    assert match.has_player(BO)
    assert not match.has_player(3)


def test_match_points_for_someone_else_is_rejected():
    with pytest.raises(NotInMatchError):
        make_match().match_points_for(3)


def test_forfeit_by_someone_else_is_rejected():
    with pytest.raises(NotInMatchError):
        make_match(Result.forfeit(3)).winner()


def test_matches_are_compared_by_identity_not_by_value():
    assert make_match() != make_match()


def test_a_result_can_be_entered_and_cleared():
    match = make_match()
    match.result = Result.played(2, 1)
    assert match.winner() == ANA
    match.result = None
    assert match.winner() is None
