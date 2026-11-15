"""Unit tests for finding a format by its key (NFR-RE-2)."""

import pytest

from bracketeer.domain.errors import UnknownFormatError
from bracketeer.domain.formats.registry import FORMATS, format_for
from bracketeer.domain.formats.round_robin import RoundRobin
from bracketeer.domain.formats.single_elimination import SingleElimination


@pytest.mark.parametrize(
    ("key", "expected"),
    [("round_robin", RoundRobin), ("single_elimination", SingleElimination)],
)
def test_a_key_gives_an_object_of_its_format(key, expected):
    assert isinstance(format_for(key), expected)


def test_each_lookup_gives_a_new_object():
    assert format_for("round_robin") is not format_for("round_robin")


def test_every_format_is_listed_under_its_own_key():
    for key, format_class in FORMATS.items():
        assert key == format_class.key


@pytest.mark.parametrize("key", ["swiss", "", "Round_Robin", None, 3, ["round_robin"]])
def test_an_unknown_key_is_rejected(key):
    with pytest.raises(UnknownFormatError, match="Unknown tournament format"):
        format_for(key)
