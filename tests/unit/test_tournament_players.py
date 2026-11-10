"""Unit tests for registering, editing, and removing players (US-01, US-02)."""

import pytest

from bracketeer.domain.errors import (
    DuplicateNameError,
    InvalidNameError,
    InvalidRatingError,
    PlayerCountError,
    UnknownPlayerError,
)
from bracketeer.domain.tournament import MAX_PLAYERS


def test_new_tournament_has_no_players(tournament):
    assert tournament.players == ()


def test_added_player_appears_in_the_list(tournament):  # US-01 #1
    player_id = tournament.add_player("Ana")
    player = tournament.player(player_id)
    assert player.name.text == "Ana"
    assert tournament.players == (player,)


def test_ids_count_up_from_1_in_registration_order(tournament):
    ids = [tournament.add_player(name) for name in ["Ana", "Ben", "Cara"]]
    assert ids == [1, 2, 3]
    assert [p.name.text for p in tournament.players] == ["Ana", "Ben", "Cara"]


def test_rejects_a_name_already_taken_ignoring_case(tournament):  # US-01 #2
    tournament.add_player("Ana")
    with pytest.raises(DuplicateNameError):
        tournament.add_player("ana")
    assert len(tournament.players) == 1


def test_rejects_an_invalid_name(tournament):  # US-01 #3
    with pytest.raises(InvalidNameError):
        tournament.add_player("   ")
    assert tournament.players == ()


@pytest.mark.parametrize(
    "rating", [-5, "abc", 1.5, True], ids=["negative", "text", "float", "bool"]
)
def test_rejects_an_invalid_rating(tournament, rating):  # US-01 #4
    with pytest.raises(InvalidRatingError):
        tournament.add_player("Ana", rating)
    assert tournament.players == ()


def test_rating_is_optional(tournament):  # US-01 #4
    player_id = tournament.add_player("Ana")
    assert tournament.player(player_id).rating is None


def test_rejects_the_65th_player(tournament):  # US-01 #5
    for number in range(MAX_PLAYERS):
        tournament.add_player(f"Player {number}")
    with pytest.raises(PlayerCountError):
        tournament.add_player("One too many")
    assert len(tournament.players) == MAX_PLAYERS


def test_edit_changes_name_and_rating(tournament):  # US-02 #1
    player_id = tournament.add_player("Jef", 1200)
    tournament.edit_player(player_id, "Jeff", 1300)
    player = tournament.player(player_id)
    assert (player.name.text, player.rating) == ("Jeff", 1300)


def test_edit_can_change_only_the_case_of_a_name(tournament):
    player_id = tournament.add_player("ana")
    tournament.edit_player(player_id, "Ana", None)
    assert tournament.player(player_id).name.text == "Ana"


def test_edit_rejects_another_players_name(tournament):  # US-02 #1
    tournament.add_player("Ana")
    ben = tournament.add_player("Ben")
    with pytest.raises(DuplicateNameError):
        tournament.edit_player(ben, "ANA", None)
    assert tournament.player(ben).name.text == "Ben"


def test_a_failed_edit_changes_nothing(tournament):
    player_id = tournament.add_player("Ana", 1500)
    with pytest.raises(InvalidRatingError):
        tournament.edit_player(player_id, "Anna", -1)
    player = tournament.player(player_id)
    assert (player.name.text, player.rating) == ("Ana", 1500)


def test_player_keeps_its_identity_when_edited(tournament):
    player_id = tournament.add_player("Jef")
    before = tournament.player(player_id)
    tournament.edit_player(player_id, "Jeff", None)
    assert tournament.player(player_id) is before


def test_removed_player_disappears(tournament):  # US-02 #2
    ana = tournament.add_player("Ana")
    ben = tournament.add_player("Ben")
    tournament.remove_player(ana)
    assert [p.id for p in tournament.players] == [ben]


def test_ids_are_never_reused(tournament):
    ana = tournament.add_player("Ana")
    tournament.remove_player(ana)
    assert tournament.add_player("Ana") == 2


def test_unknown_player_id_is_rejected(tournament):
    with pytest.raises(UnknownPlayerError):
        tournament.player(99)
    with pytest.raises(UnknownPlayerError):
        tournament.edit_player(99, "Ana", None)
    with pytest.raises(UnknownPlayerError):
        tournament.remove_player(99)
