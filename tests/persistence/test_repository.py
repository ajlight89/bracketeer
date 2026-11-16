"""Tests for saving and opening tournament files (US-10, NFR-RE-1 to NFR-RE-3)."""

import json
import os

import pytest

from bracketeer.domain.formats.round_robin import RoundRobin
from bracketeer.domain.tournament import Tournament
from bracketeer.domain.values import Result
from bracketeer.persistence.errors import (
    DamagedFileError,
    NewerVersionError,
    SaveFileError,
)
from bracketeer.persistence.repository import TournamentRepository
from bracketeer.persistence.save_format import FORMAT_VERSION, tournament_to_data


@pytest.fixture
def repository():
    return TournamentRepository()


def test_a_saved_tournament_opens_exactly_as_it_was(repository, league, tmp_path):
    # US-10 #1
    path = tmp_path / "league.json"
    repository.save(league, path)
    loaded = repository.load(path)
    assert tournament_to_data(loaded) == tournament_to_data(league)
    assert loaded.standings() == league.standings()


def test_the_file_is_json_with_a_format_version(repository, league, tmp_path):
    # NFR-RE-3
    path = tmp_path / "league.json"
    repository.save(league, path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["format_version"] == FORMAT_VERSION
    assert data["name"] == "Friday Smash Night"


def test_names_with_accents_are_saved_as_written(repository, tmp_path):
    # The file is always UTF-8, whatever the computer's default encoding is.
    tournament = Tournament("Café Cup", RoundRobin())
    tournament.add_player("Zoë")
    path = tmp_path / "cafe.json"
    repository.save(tournament, path)
    assert "Zoë" in path.read_text(encoding="utf-8")
    assert repository.load(path).players[0].name.text == "Zoë"


def test_saving_again_replaces_the_file(repository, league, tmp_path):
    path = tmp_path / "league.json"
    repository.save(league, path)
    league.record_result(league.rounds[2].matches[0].id, Result.played(2, 0))
    repository.save(league, path)
    assert tournament_to_data(repository.load(path)) == tournament_to_data(league)
    assert list(tmp_path.iterdir()) == [path]


def test_a_failed_save_keeps_the_previous_file(
    repository, league, tmp_path, monkeypatch
):
    # NFR-RE-1: the save fails after part of the new file is written.
    path = tmp_path / "league.json"
    repository.save(league, path)
    before = path.read_bytes()
    league.record_result(league.rounds[2].matches[0].id, Result.played(2, 0))

    def disk_full(file_descriptor):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(os, "fsync", disk_full)
    with pytest.raises(SaveFileError, match="No space left on device"):
        repository.save(league, path)
    assert path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [path]  # no temporary file left behind


def test_saving_into_a_missing_folder_shows_a_message(repository, league, tmp_path):
    path = tmp_path / "missing" / "league.json"
    with pytest.raises(SaveFileError, match="Couldn't save"):
        repository.save(league, path)
    assert not path.parent.exists()


def test_opening_a_missing_file_shows_a_message(repository, tmp_path):
    with pytest.raises(SaveFileError, match="Couldn't open") as caught:
        repository.load(tmp_path / "nothing.json")
    assert caught.type is SaveFileError


@pytest.mark.parametrize(
    "content",
    [
        pytest.param(b"", id="empty"),
        pytest.param(b"not json at all", id="text"),
        pytest.param(b"\xff\xfe\x00\x81", id="not-text"),
        pytest.param(b"[]", id="list"),
        pytest.param(b'{"format_version": 1}', id="almost-empty"),
        pytest.param(b"[" * 100_000 + b"]" * 100_000, id="deeply-nested"),
    ],
)
def test_a_damaged_file_shows_a_message_and_isnt_changed(repository, tmp_path, content):
    # US-10 #4, NFR-RE-2
    path = tmp_path / "damaged.json"
    path.write_bytes(content)
    with pytest.raises(DamagedFileError, match="^The file is damaged"):
        repository.load(path)
    assert path.read_bytes() == content


def test_a_cut_off_file_shows_a_message_and_isnt_changed(repository, league, tmp_path):
    # US-10 #4, NFR-RE-2
    path = tmp_path / "league.json"
    repository.save(league, path)
    content = path.read_bytes()[:-40]
    path.write_bytes(content)
    with pytest.raises(DamagedFileError, match="isn't valid JSON"):
        repository.load(path)
    assert path.read_bytes() == content


def test_a_file_from_a_newer_version_is_refused(repository, league, tmp_path):
    # US-10 #5, NFR-RE-3
    data = tournament_to_data(league)
    data["format_version"] = FORMAT_VERSION + 1
    path = tmp_path / "newer.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(NewerVersionError, match="newer version of Bracketeer"):
        repository.load(path)
