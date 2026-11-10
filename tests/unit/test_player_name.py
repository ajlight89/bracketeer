"""Unit tests for the PlayerName value object (R-PL-2)."""

import dataclasses

import pytest

from bracketeer.domain.errors import DomainError, InvalidNameError
from bracketeer.domain.values import PlayerName


def test_keeps_a_valid_name():
    assert PlayerName("Ana").text == "Ana"


def test_trims_leading_and_trailing_spaces():
    assert PlayerName(" Ana ").text == "Ana"


def test_accepts_exactly_40_characters():
    assert PlayerName("x" * 40).text == "x" * 40


def test_counts_length_after_trimming():
    assert PlayerName(" " + "x" * 40 + " ").text == "x" * 40


@pytest.mark.parametrize(
    "raw",
    ["", " ", "x" * 41],
    ids=["empty", "only spaces", "41 characters"],
)
def test_rejects_empty_or_too_long_names(raw):
    with pytest.raises(InvalidNameError):
        PlayerName(raw)


def test_invalid_name_error_is_a_domain_error():
    assert issubclass(InvalidNameError, DomainError)


def test_key_ignores_case():
    assert PlayerName("Ana").key() == PlayerName("ANA").key()


def test_names_with_equal_text_are_equal():
    assert PlayerName("Ana") == PlayerName(" Ana ")


def test_cannot_be_changed_after_creation():
    name = PlayerName("Ana")
    with pytest.raises(dataclasses.FrozenInstanceError):
        name.text = "Bob"
