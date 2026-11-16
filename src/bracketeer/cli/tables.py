"""Text tables and status lines that fit an 80-column terminal (NFR-US-3).

These functions only build lines of text; the menus print them.
"""

import textwrap

from bracketeer.app.session import TournamentSession

WIDTH = 80
NAME_WIDTH = 40  # The longest name allowed (R-PL-2).
MATCH_NAME_WIDTH = 30  # Two names and a result share one line.

# The order here is the order of the format menu.
FORMAT_NAMES = {
    "single_elimination": "Single elimination",
    "round_robin": "Round robin",
}

STANDINGS_KEY = (
    "P played, W won, D drawn, L lost, Pts match points, GD game differential"
)
FORFEIT_KEY = "F forfeited, W won by forfeit"


def fit(text: str, width: int) -> str:
    """Shorten text to width characters, ending with "…" if it was cut."""
    if len(text) <= width:
        return text
    return text[: width - 1] + "…"


def plural(count: int, word: str) -> str:
    """Return "1 match", "2 matches", "3 players", and so on."""
    if count == 1:
        return f"{count} {word}"
    ending = "es" if word.endswith("ch") else "s"
    return f"{count} {word}{ending}"


def player_lines(players) -> list[str]:
    """Return a table of players, numbered in the order given."""
    lines = [f"{'#':>4}  {'Name':<{NAME_WIDTH}}  {'Rating':>6}  {'Seed':>4}"]
    for number, player in enumerate(players, start=1):
        name = fit(player.name.text, NAME_WIDTH)
        rating = "" if player.rating is None else player.rating
        seed = "" if player.seed is None else player.seed
        lines.append(
            f"{number:>4}  {name:<{NAME_WIDTH}}  {rating:>6}  {seed:>4}".rstrip()
        )
    return lines


def round_lines(tournament, round_) -> list[str]:
    """Return a table of one round's matches, then its byes."""
    width = MATCH_NAME_WIDTH
    lines = [f"{'#':>4}  {'Player':>{width}}  {'Result':^7}  Player"]
    has_forfeit = False
    for number, match in enumerate(round_.matches, start=1):
        name_a = fit(_name(tournament, match.player_a), width)
        name_b = fit(_name(tournament, match.player_b), width)
        result = result_text(match)
        lines.append(f"{number:>4}  {name_a:>{width}}  {result:^7}  {name_b}")
        if match.result is not None and match.result.forfeited_by is not None:
            has_forfeit = True
    if round_.byes:
        byes = ", ".join(_name(tournament, player_id) for player_id in round_.byes)
        lines.extend(
            textwrap.wrap(f"Bye: {byes}", WIDTH - 1, subsequent_indent="     ")
        )
    if has_forfeit:
        lines.append(FORFEIT_KEY)
    return lines


def result_text(match) -> str:
    """Return "2 - 1", "vs" for no result, or "F - W" for a forfeit."""
    result = match.result
    if result is None:
        return "vs"
    if result.forfeited_by is None:
        return f"{result.score_a} - {result.score_b}"
    if result.forfeited_by == match.player_a:
        return "F - W"
    return "W - F"


def standings_lines(tournament) -> list[str]:
    """Return the standings table, then the key to its columns (US-09 #6)."""
    lines = [
        f"{'Rank':>4}  {'Name':<{NAME_WIDTH}}  {'P':>3} {'W':>3} {'D':>3} "
        f"{'L':>3} {'Pts':>4} {'GD':>4}"
    ]
    for row in tournament.standings():
        name = fit(_name(tournament, row.player_id), NAME_WIDTH)
        lines.append(
            f"{row.rank:>4}  {name:<{NAME_WIDTH}}  {row.played():>3} {row.wins:>3} "
            f"{row.draws:>3} {row.losses:>3} {row.match_points:>4} "
            f"{signed(row.game_differential):>4}"
        )
    lines.append(STANDINGS_KEY)
    return lines


def signed(number: int) -> str:
    """Return +3, -2, or 0."""
    return f"{number:+d}" if number else "0"


def status_lines(session: TournamentSession) -> list[str]:
    """Return the format, progress, and file of the open tournament."""
    tournament = session.tournament
    format_name = FORMAT_NAMES.get(tournament.format.key, tournament.format.key)
    players = plural(len(tournament.players), "player")
    if session.path is None:
        file = "not saved yet"
    elif session.has_unsaved_changes:
        file = f"{session.path.name} (unsaved changes)"
    else:
        file = session.path.name
    return [
        fit(f"{format_name}, {players}, {progress(tournament)}", WIDTH),
        fit(f"File: {file}", WIDTH),
    ]


def progress(tournament) -> str:
    """Return "not started", "round 2 in progress", or the champion."""
    if not tournament.started:
        return "not started"
    if tournament.is_complete():
        return f"complete, champion: {champion(tournament)}"
    return f"round {current_round(tournament).number} in progress"


def champion(tournament) -> str:
    """Return the name of the player ranked first."""
    return _name(tournament, tournament.standings()[0].player_id)


def current_round(tournament):
    """Return the first round still missing a result, or else the last round."""
    for round_ in tournament.rounds:
        if not round_.is_finished():
            return round_
    return tournament.rounds[-1]


def _name(tournament, player_id) -> str:
    return tournament.player(player_id).name.text
