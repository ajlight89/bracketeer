"""Unit tests for the Result value object (R-RS-1, R-RS-5)."""

import dataclasses

import pytest

from bracketeer.domain.errors import DomainError, InvalidResultError
from bracketeer.domain.values import Result, ResultKind


def test_played_result_keeps_its_scores():
    result = Result.played(2, 1)
    assert result.kind is ResultKind.PLAYED
    assert (result.score_a, result.score_b) == (2, 1)
    assert result.forfeited_by is None


def test_zero_is_a_valid_score():
    assert Result.played(0, 0).score_a == 0


@pytest.mark.parametrize(
    ("score_a", "score_b"),
    [(-1, 0), (0, -1), (1.5, 0), ("2", 0), (True, 0), (None, 0)],
    ids=["negative a", "negative b", "float", "string", "bool", "missing"],
)
def test_rejects_invalid_game_scores(score_a, score_b):
    with pytest.raises(InvalidResultError):
        Result.played(score_a, score_b)


def test_equal_scores_are_a_draw():
    assert Result.played(2, 2).is_draw()


def test_unequal_scores_are_not_a_draw():
    assert not Result.played(2, 1).is_draw()


def test_forfeit_records_who_forfeited():
    result = Result.forfeit(3)
    assert result.kind is ResultKind.FORFEIT
    assert result.forfeited_by == 3
    assert (result.score_a, result.score_b) == (None, None)


def test_forfeit_is_never_a_draw():
    assert not Result.forfeit(3).is_draw()


@pytest.mark.parametrize(
    "fields",
    [
        {"kind": ResultKind.PLAYED, "score_a": 1, "score_b": 0, "forfeited_by": 3},
        {"kind": ResultKind.FORFEIT, "forfeited_by": None},
        {"kind": ResultKind.FORFEIT, "score_a": 1, "score_b": 0, "forfeited_by": 3},
        {"kind": "played", "score_a": 1, "score_b": 0},
    ],
    ids=[
        "played with forfeiter",
        "forfeit without forfeiter",
        "forfeit with scores",
        "kind not a ResultKind",
    ],
)
def test_rejects_invalid_shapes(fields):
    with pytest.raises(InvalidResultError):
        Result(**fields)


def test_results_with_equal_values_are_equal():
    assert Result.played(2, 1) == Result.played(2, 1)


def test_cannot_be_changed_after_creation():
    result = Result.played(2, 1)
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.score_a = 3


def test_invalid_result_error_is_a_domain_error():
    assert issubclass(InvalidResultError, DomainError)
