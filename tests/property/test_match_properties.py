"""Property-based tests for match points (R-RS-1, R-RS-3)."""

from hypothesis import given
from hypothesis import strategies as st

from bracketeer.domain.rounds import Match
from bracketeer.domain.values import Result

scores = st.integers(min_value=0, max_value=1_000)


@given(scores, scores)
def test_played_match_hands_out_points_by_score(score_a, score_b):
    match = Match(1, 1, 2, Result.played(score_a, score_b))
    points = (match.match_points_for(1), match.match_points_for(2))
    if score_a > score_b:
        assert points == (3, 0)
    elif score_a < score_b:
        assert points == (0, 3)
    else:
        assert points == (1, 1)
