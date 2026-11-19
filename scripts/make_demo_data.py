"""Create sample tournaments for the report's screenshots.

Run it from the repository folder with the virtual environment active:

    python scripts\\make_demo_data.py               # into Documents\\Bracketeer
    python scripts\\make_demo_data.py --replace     # also replace existing files
    python scripts\\make_demo_data.py --folder demo # into another folder

Every tournament is built through the app layer, the same way the menus build
one, so every file follows the tournament rules. The scores are fixed, so every
run makes the same tournaments.
"""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from bracketeer.app.session import DEFAULT_FOLDER, TournamentSession
from bracketeer.domain.rounds import Match, Round
from bracketeer.domain.tournament import Tournament
from bracketeer.domain.values import PlayerId

FILE_EXTENSION = ".bracketeer"

# Made-up gamer tags and ratings.
CUP_PLAYERS = [
    ("NovaStrike", 1850),
    ("PixelPaladin", 1720),
    ("ByteKnight", 1640),
    ("LunarLynx", 1580),
    ("ComboQueen", 1495),
    ("GlitchGoblin", 1410),
]
LEAGUE_PLAYERS = [
    ("AceVortex", 1900),
    ("ShadowFox", 1810),
    ("TurboTaco", 1760),
    ("QuietStorm", 1690),
    ("MeteorMae", 1600),
    ("RetroRaven", 1530),
]
SIGNUP_PLAYERS = [
    ("KiloWatt", 1550),
    ("SnackAttack", None),
    ("DriftQueen", 1720),
    ("MossyMage", 1480),
    ("ZapZilla", 1610),
]


# Building blocks


def add_players(session: TournamentSession, players) -> None:
    for name, rating in players:
        session.add_player(name, rating)


def player_id(tournament: Tournament, name: str) -> PlayerId:
    for player in tournament.players:
        if player.name.text == name:
            return player.id
    raise ValueError(f"No player named {name}.")


def find_match(
    tournament: Tournament, rounds: Sequence[Round], name_a: str, name_b: str
) -> Match:
    """Return the match between two players in the given rounds."""
    wanted = {player_id(tournament, name_a), player_id(tournament, name_b)}
    for round_ in rounds:
        for match in round_.matches:
            if {match.player_a, match.player_b} == wanted:
                return match
    raise ValueError(f"No match between {name_a} and {name_b}.")


def play(session: TournamentSession, results, round_number=None) -> None:
    """Record results given as (player, player, their score, their score).

    The players can be listed in either order. Without a round number, the
    match is looked for in every round, which suits round robin.
    """
    tournament = session.tournament
    rounds = tournament.rounds
    if round_number is not None:
        rounds = [rounds[round_number - 1]]
    for name_a, name_b, score_a, score_b in results:
        match = find_match(tournament, rounds, name_a, name_b)
        if match.player_a == player_id(tournament, name_a):
            session.record_score(match.id, score_a, score_b)
        else:
            session.record_score(match.id, score_b, score_a)


def forfeit(session: TournamentSession, round_number: int, name: str) -> None:
    """Record that a player forfeited their match in a round."""
    tournament = session.tournament
    forfeiting = player_id(tournament, name)
    for match in tournament.rounds[round_number - 1].matches:
        if forfeiting in (match.player_a, match.player_b):
            session.record_forfeit(match.id, forfeiting)
            return
    raise ValueError(f"{name} has no match in round {round_number}.")


# The tournaments for the screenshots


def campus_cup(session: TournamentSession, finished: bool) -> None:
    """Single elimination, 6 players: the top two seeds get byes (R-SE-1)."""
    session.new("Campus Cup", "single_elimination")
    add_players(session, CUP_PLAYERS)
    session.seed_by_rating()
    session.start()
    play(
        session,
        [("LunarLynx", "ComboQueen", 1, 2), ("ByteKnight", "GlitchGoblin", 2, 0)],
        round_number=1,
    )
    session.generate_next_round()
    play(session, [("NovaStrike", "ComboQueen", 2, 0)], round_number=2)
    if not finished:
        return  # Round 2 stays in progress.
    forfeit(session, 2, "PixelPaladin")
    session.generate_next_round()
    play(session, [("NovaStrike", "ByteKnight", 2, 3)], round_number=3)


def campus_cup_round_2(session: TournamentSession) -> None:
    campus_cup(session, finished=False)


def campus_cup_complete(session: TournamentSession) -> None:
    campus_cup(session, finished=True)


def thursday_league(session: TournamentSession) -> None:
    """Round robin, 6 players, complete, with both tiebreakers in use.

    TurboTaco and ShadowFox both have 10 points; TurboTaco ranks higher on
    game differential (+5 to +2). QuietStorm and MeteorMae both have 6 points
    and -2; QuietStorm ranks higher on seed, 4 to 5 (R-TB-2, R-TB-3).
    """
    session.new("Thursday League", "round_robin")
    add_players(session, LEAGUE_PLAYERS)
    session.seed_by_rating()
    session.start()
    play(
        session,
        [
            ("AceVortex", "ShadowFox", 2, 1),
            ("AceVortex", "TurboTaco", 2, 1),
            ("AceVortex", "QuietStorm", 1, 2),
            ("AceVortex", "MeteorMae", 2, 0),
            ("AceVortex", "RetroRaven", 2, 0),
            ("ShadowFox", "TurboTaco", 1, 1),
            ("ShadowFox", "QuietStorm", 2, 1),
            ("ShadowFox", "MeteorMae", 2, 1),
            ("ShadowFox", "RetroRaven", 2, 1),
            ("TurboTaco", "QuietStorm", 2, 0),
            ("TurboTaco", "MeteorMae", 2, 0),
            ("TurboTaco", "RetroRaven", 2, 0),
            ("QuietStorm", "MeteorMae", 1, 2),
            ("QuietStorm", "RetroRaven", 2, 1),
            ("MeteorMae", "RetroRaven", 2, 0),
        ],
    )


def game_night_signups(session: TournamentSession) -> None:
    """Round robin, 5 players, not seeded or started yet: for the setup screens."""
    session.new("Game Night Signups", "round_robin")
    add_players(session, SIGNUP_PLAYERS)


# Each file's name, without the extension, and how it's built. The Open list
# shows the newest file first, so the last one here is on top.
DEMO_FILES = [
    ("Game Night Signups", game_night_signups),
    ("Thursday League", thursday_league),
    ("Campus Cup (round 2)", campus_cup_round_2),
    ("Campus Cup", campus_cup_complete),
]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create sample tournaments for the report's screenshots."
    )
    parser.add_argument(
        "--folder",
        type=Path,
        default=DEFAULT_FOLDER,
        help=f"where to write the files (default: {DEFAULT_FOLDER})",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="replace files that already exist (default: keep them)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    for name, build in DEMO_FILES:
        path = args.folder / f"{name}{FILE_EXTENSION}"
        if path.exists() and not args.replace:
            print(f"Kept {path} (it already exists; --replace replaces it).")
            continue
        args.folder.mkdir(parents=True, exist_ok=True)
        session = TournamentSession()
        build(session)
        session.save(path)
        print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
