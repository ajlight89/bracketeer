"""Property-based tests for PlayerName (R-PL-2)."""

from hypothesis import given
from hypothesis import strategies as st

from bracketeer.domain.values import PlayerName

# Valid names: 1-40 characters with no whitespace at either end.
valid_names = st.text(min_size=1, max_size=40).filter(lambda s: s == s.strip())

# Whitespace to wrap around a name.
padding = st.text(alphabet=" \t", max_size=5)


@given(valid_names, padding, padding)
def test_whitespace_around_a_name_is_ignored(text, before, after):
    assert PlayerName(before + text + after) == PlayerName(text)
