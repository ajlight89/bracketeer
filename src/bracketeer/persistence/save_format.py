"""Convert a tournament to and from the data stored in a saved file.

Saving keeps only the facts: the players, their seeds, the rounds, and the
results. Opening rebuilds the tournament by replaying those facts through
Tournament's public methods (decision 11 in docs/key-decisions.md), so every
domain rule checks the file again on the way in.
"""

from typing import Any

from bracketeer.domain.errors import DomainError
from bracketeer.domain.formats.registry import format_for
from bracketeer.domain.rounds import Match, Round
from bracketeer.domain.tournament import Tournament
from bracketeer.domain.values import PlayerId, Result, ResultKind, is_non_negative_int
from bracketeer.persistence.errors import DamagedFileError, NewerVersionError

# Raise this when the layout of the saved data changes (NFR-RE-3).
FORMAT_VERSION = 1


def tournament_to_data(tournament: Tournament) -> dict[str, Any]:
    """Return the tournament as plain dicts and lists, ready for JSON."""
    return {
        "format_version": FORMAT_VERSION,
        "name": tournament.name,
        "format": tournament.format.key,
        "started": tournament.started,
        "players": [
            {"id": p.id, "name": p.name.text, "rating": p.rating, "seed": p.seed}
            for p in tournament.players
        ],
        "rounds": [_round_to_data(round_) for round_ in tournament.rounds],
    }


def _round_to_data(round_: Round) -> dict[str, Any]:
    return {
        "number": round_.number,
        "byes": list(round_.byes),
        "matches": [_match_to_data(match) for match in round_.matches],
    }


def _match_to_data(match: Match) -> dict[str, Any]:
    return {
        "id": match.id,
        "player_a": match.player_a,
        "player_b": match.player_b,
        "result": _result_to_data(match.result),
    }


def _result_to_data(result: Result | None) -> dict[str, Any] | None:
    if result is None:
        return None
    if result.kind is ResultKind.FORFEIT:
        return {"kind": result.kind.value, "forfeited_by": result.forfeited_by}
    return {
        "kind": result.kind.value,
        "score_a": result.score_a,
        "score_b": result.score_b,
    }


def tournament_from_data(data: object) -> Tournament:
    """Rebuild a tournament from a saved file's data (NFR-RE-2, NFR-SE-4).

    The data is untrusted, so each value's type is checked before it's used,
    and the domain checks every rule while the tournament is replayed. Any
    problem raises DamagedFileError; a newer file raises NewerVersionError.
    """
    file = _object(data, "the file")
    _check_version(_field(file, "format_version", "the file"))
    try:
        return _replay(file)
    except DomainError as error:
        raise DamagedFileError(str(error)) from error


def _check_version(version: object) -> None:
    if not is_non_negative_int(version) or version == 0:
        raise DamagedFileError("format_version should be a whole number above 0.")
    if version > FORMAT_VERSION:
        raise NewerVersionError(
            f"This file was saved by a newer version of Bracketeer (file format "
            f"{version}). This version can only open file format {FORMAT_VERSION}."
        )


def _replay(file: dict[str, Any]) -> Tournament:
    """Rebuild the tournament step by step through its public methods."""
    name = _text(_field(file, "name", "the file"), "name")
    tournament = Tournament(name, format_for(_field(file, "format", "the file")))
    players = _list(_field(file, "players", "the file"), "players")
    new_ids = _replay_players(tournament, players)
    started = _bool(_field(file, "started", "the file"), "started")
    rounds = _list(_field(file, "rounds", "the file"), "rounds")
    if not started:
        if rounds:
            raise DamagedFileError("A tournament that hasn't started has no rounds.")
        return tournament
    tournament.start()
    _replay_rounds(tournament, rounds, new_ids)
    return tournament


def _replay_players(
    tournament: Tournament, saved_players: list[Any]
) -> dict[int, PlayerId]:
    """Add and seed the saved players; return a map of saved ID to new ID.

    A player removed before the start leaves a gap in the saved IDs, while
    the rebuilt tournament numbers its players 1, 2, 3, ... again. The map
    translates every player ID found later in the file.
    """
    new_ids: dict[int, PlayerId] = {}
    seeded: list[tuple[int, PlayerId]] = []
    for index, value in enumerate(saved_players):
        where = f"players[{index}]"
        saved = _object(value, where)
        saved_id = _whole_number(_field(saved, "id", where), f"{where}.id")
        if saved_id in new_ids:
            raise DamagedFileError(f"Two players have the ID {saved_id}.")
        name = _text(_field(saved, "name", where), f"{where}.name")
        rating = _field(saved, "rating", where)
        seed = _field(saved, "seed", where)
        rating = _optional_whole_number(rating, f"{where}.rating")
        seed = _optional_whole_number(seed, f"{where}.seed")
        new_ids[saved_id] = tournament.add_player(name, rating)
        if seed is not None:
            seeded.append((seed, new_ids[saved_id]))
    if seeded:
        seeds = sorted(seed for seed, _ in seeded)
        if seeds != list(range(1, len(saved_players) + 1)):
            raise DamagedFileError(
                "The seeds should number every player 1, 2, 3, ... with no gaps."
            )
        tournament.seed_manually([player_id for _, player_id in sorted(seeded)])
    return new_ids


def _replay_rounds(
    tournament: Tournament, saved_rounds: list[Any], new_ids: dict[int, PlayerId]
) -> None:
    """Record each saved round's results, adding rounds as the format would.

    Round robin plans every round at the start; single elimination adds a
    round only once the one before it is finished. Either way, each rebuilt
    round must be the round stored in the file.
    """
    for index, value in enumerate(saved_rounds):
        where = f"rounds[{index}]"
        saved = _object(value, where)
        if index == len(tournament.rounds):
            tournament.generate_next_round()
        round_ = tournament.rounds[index]
        match_list = _list(_field(saved, "matches", where), f"{where}.matches")
        saved_matches = [
            _object(match, f"{where}.matches[{n}]")
            for n, match in enumerate(match_list)
        ]
        _check_same_round(round_, saved, saved_matches, new_ids, where)
        pairs = zip(round_.matches, saved_matches, strict=True)
        for n, (match, saved_match) in enumerate(pairs):
            match_where = f"{where}.matches[{n}]"
            result_value = _field(saved_match, "result", match_where)
            result = _result(result_value, new_ids, f"{match_where}.result")
            if result is not None:
                tournament.record_result(match.id, result)
    if len(saved_rounds) != len(tournament.rounds):
        raise DamagedFileError(
            f"The file has {len(saved_rounds)} rounds, but this tournament "
            f"has {len(tournament.rounds)}."
        )


def _check_same_round(
    round_: Round,
    saved: dict[str, Any],
    saved_matches: list[dict[str, Any]],
    new_ids: dict[int, PlayerId],
    where: str,
) -> None:
    """Raise unless the rebuilt round has the saved number, byes, and matches."""
    number = _whole_number(_field(saved, "number", where), f"{where}.number")
    saved_byes = _list(_field(saved, "byes", where), f"{where}.byes")
    byes = [
        _player(value, new_ids, f"{where}.byes[{n}]")
        for n, value in enumerate(saved_byes)
    ]
    matches = []
    for n, saved_match in enumerate(saved_matches):
        match_where = f"{where}.matches[{n}]"
        match_id = _field(saved_match, "id", match_where)
        player_a = _field(saved_match, "player_a", match_where)
        player_b = _field(saved_match, "player_b", match_where)
        matches.append(
            (
                _whole_number(match_id, f"{match_where}.id"),
                _player(player_a, new_ids, f"{match_where}.player_a"),
                _player(player_b, new_ids, f"{match_where}.player_b"),
            )
        )
    rebuilt = [(m.id, m.player_a, m.player_b) for m in round_.matches]
    if number != round_.number or byes != round_.byes or matches != rebuilt:
        raise DamagedFileError(
            f"Round {round_.number} in the file isn't the round the "
            "tournament's rules produce."
        )


def _result(value: object, new_ids: dict[int, PlayerId], where: str) -> Result | None:
    """Return the saved result, or None if the match has no result yet."""
    if value is None:
        return None
    saved = _object(value, where)
    kind = _field(saved, "kind", where)
    if kind == ResultKind.PLAYED.value:
        score_a = _field(saved, "score_a", where)
        score_b = _field(saved, "score_b", where)
        return Result.played(
            _whole_number(score_a, f"{where}.score_a"),
            _whole_number(score_b, f"{where}.score_b"),
        )
    if kind == ResultKind.FORFEIT.value:
        forfeited_by = _field(saved, "forfeited_by", where)
        return Result.forfeit(_player(forfeited_by, new_ids, f"{where}.forfeited_by"))
    raise DamagedFileError(f'{where}.kind should be "played" or "forfeit".')


# Type checks: each returns the value if it has the expected type.


def _field(saved: dict[str, Any], key: str, where: str) -> Any:
    if key not in saved:
        raise DamagedFileError(f'"{key}" is missing from {where}.')
    return saved[key]


def _object(value: object, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DamagedFileError(f"{where} should be an object.")
    return value


def _list(value: object, where: str) -> list[Any]:
    if not isinstance(value, list):
        raise DamagedFileError(f"{where} should be a list.")
    return value


def _text(value: object, where: str) -> str:
    if not isinstance(value, str):
        raise DamagedFileError(f"{where} should be text.")
    return value


def _bool(value: object, where: str) -> bool:
    if not isinstance(value, bool):
        raise DamagedFileError(f"{where} should be true or false.")
    return value


def _whole_number(value: object, where: str) -> int:
    if not is_non_negative_int(value):
        raise DamagedFileError(f"{where} should be a whole number of 0 or more.")
    return value


def _optional_whole_number(value: object, where: str) -> int | None:
    if value is None:
        return None
    return _whole_number(value, where)


def _player(value: object, new_ids: dict[int, PlayerId], where: str) -> PlayerId:
    """Return the new ID of the saved player this value refers to."""
    saved_id = _whole_number(value, where)
    if saved_id not in new_ids:
        raise DamagedFileError(f"{where} refers to player {saved_id}, who isn't there.")
    return new_ids[saved_id]
