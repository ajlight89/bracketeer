"""Unit tests for the Player entity."""

from bracketeer.domain.player import Player
from bracketeer.domain.values import PlayerName


def test_players_are_compared_by_identity_not_by_value():
    first = Player(1, PlayerName("Ana"))
    second = Player(1, PlayerName("Ana"))
    assert first != second
    assert first == first


def test_players_can_be_used_in_sets():
    ana = Player(1, PlayerName("Ana"))
    assert ana in {ana}
