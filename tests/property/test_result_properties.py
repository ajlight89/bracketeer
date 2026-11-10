"""Property-based tests for Result (R-RS-1)."""

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from bracketeer.domain.errors import InvalidResultError
from bracketeer.domain.values import Result

scores = st.integers(min_value=0)


@given(scores, scores)
@example(0, 0)
def test_any_two_valid_scores_make_a_result(score_a, score_b):
    result = Result.played(score_a, score_b)
    assert result.is_draw() == (score_a == score_b)


@given(st.integers(max_value=-1), scores)
def test_a_negative_score_is_always_rejected(negative, other):
    with pytest.raises(InvalidResultError):
        Result.played(negative, other)
