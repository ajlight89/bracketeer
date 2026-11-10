"""Shared pytest fixtures for all test folders."""

import pytest

from bracketeer.domain.formats.round_robin import RoundRobin
from bracketeer.domain.tournament import Tournament


@pytest.fixture
def tournament():
    """A new, empty tournament for each test."""
    return Tournament("Friday Smash Night", RoundRobin())
