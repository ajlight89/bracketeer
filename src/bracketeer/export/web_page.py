"""Export a tournament as a single, self-contained web page (US-11).

The page is one HTML file with its styles inside it: no scripts, no images,
and no links to other files or websites. It opens offline in any browser and
can be emailed or posted as it is (NFR-PO-3).

Every name the organizer typed goes through html.escape before it is placed
in the page, so a player named <script>alert(1)</script> is shown as text and
never run (NFR-SE-2). Numbers come from the rules, not from typing, so they
need no escaping.
"""

from datetime import datetime
from html import escape
from pathlib import Path

from bracketeer.domain.rounds import Match, Round
from bracketeer.domain.tournament import Tournament
from bracketeer.domain.values import PlayerId

# The same names the menus show.
FORMAT_NAMES = {
    "single_elimination": "Single elimination",
    "round_robin": "Round robin",
}

STANDINGS_KEY = (
    "P played, W won, D drawn, L lost, Pts match points, GD game differential"
)
FORFEIT_KEY = "F forfeited, W won by forfeit"

STYLE = """
body {
  font-family: "Segoe UI", system-ui, sans-serif;
  max-width: 52rem;
  margin: 2rem auto;
  padding: 0 1rem;
  line-height: 1.4;
  color: #1f2328;
  background: #ffffff;
}
h1 { margin-bottom: 0.25rem; }
.summary { margin-top: 0; color: #59636e; }
.champion {
  font-size: 1.25rem;
  font-weight: 600;
  padding: 0.5rem 0.75rem;
  border-left: 4px solid #1a7f37;
  background: #dafbe1;
}
table { border-collapse: collapse; width: 100%; margin: 0.5rem 0; }
th, td { padding: 0.35rem 0.6rem; border-bottom: 1px solid #d1d9e0; }
td { overflow-wrap: anywhere; }
th { background: #f6f8fa; }
.standings th, .standings td { text-align: right; }
.standings th:nth-child(2), .standings td:nth-child(2) {
  text-align: left;
  width: 100%;
}
.matches { table-layout: fixed; }
.matches td:first-child { text-align: right; width: 45%; }
.matches .result { text-align: center; width: 10%; white-space: nowrap; }
.winner { font-weight: 600; }
.note, footer { color: #59636e; font-size: 0.9rem; }
footer { margin-top: 2rem; }
@media (prefers-color-scheme: dark) {
  body { color: #e6edf3; background: #0d1117; }
  th { background: #161b22; }
  th, td { border-color: #3d444d; }
  .summary, .note, footer { color: #9198a1; }
  .champion { background: #12261e; border-color: #3fb950; }
}
"""


def write_web_page(tournament: Tournament, path: Path, exported_at: datetime) -> None:
    """Write the page to path, as UTF-8 whatever the computer's default is."""
    page = web_page(tournament, exported_at)
    path.write_text(page, encoding="utf-8", newline="\n")


def web_page(tournament: Tournament, exported_at: datetime) -> str:
    """Return the tournament as a complete HTML document.

    exported_at is passed in, rather than read from the clock here, so a test
    gets the same page every time.
    """
    if not tournament.started:
        raise ValueError("Only a tournament that has started can be exported.")
    title = escape(tournament.name)
    lines = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{title}</title>",
        f"<style>{STYLE}</style>",
        "</head>",
        "<body>",
        f"<h1>{title}</h1>",
        f'<p class="summary">{summary(tournament)}</p>',
    ]
    if tournament.is_complete():
        champion = _name(tournament, tournament.standings()[0].player_id)
        lines.append(f'<p class="champion">Champion: {champion}</p>')
    lines.extend(standings_table(tournament))
    lines.append("<h2>Rounds</h2>")
    for round_ in tournament.rounds:
        lines.extend(round_table(tournament, round_))
    lines.extend(
        [
            f"<footer>Exported from Bracketeer on "
            f"{exported_at:%Y-%m-%d} at {exported_at:%H:%M}.</footer>",
            "</body>",
            "</html>",
        ]
    )
    return "\n".join(lines) + "\n"


def summary(tournament: Tournament) -> str:
    """Return the format, the number of players, and the progress."""
    format_name = FORMAT_NAMES.get(tournament.format.key, tournament.format.key)
    count = len(tournament.players)
    players = f"{count} player" if count == 1 else f"{count} players"
    return f"{format_name} · {players} · {progress(tournament)}"


def progress(tournament: Tournament) -> str:
    """Return "complete", "round 2 in progress", or "waiting for round 3"."""
    if tournament.is_complete():
        return "complete"
    for round_ in tournament.rounds:
        if not round_.is_finished():
            return f"round {round_.number} in progress"
    return f"waiting for round {len(tournament.rounds) + 1}"


def standings_table(tournament: Tournament) -> list[str]:
    """Return the standings as an HTML table, then the key to its columns."""
    lines = [
        "<h2>Standings</h2>",
        '<table class="standings">',
        "<thead><tr><th>Rank</th><th>Name</th><th>P</th><th>W</th><th>D</th>"
        "<th>L</th><th>Pts</th><th>GD</th></tr></thead>",
        "<tbody>",
    ]
    for row in tournament.standings():
        cells = [
            row.rank,
            _name(tournament, row.player_id),
            row.played(),
            row.wins,
            row.draws,
            row.losses,
            row.match_points,
            signed(row.game_differential),
        ]
        lines.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")
    lines.extend(["</tbody>", "</table>", f'<p class="note">{STANDINGS_KEY}</p>'])
    return lines


def round_table(tournament: Tournament, round_: Round) -> list[str]:
    """Return one round's heading and matches, then its byes."""
    lines = [
        f"<h3>Round {round_.number}{round_status(round_)}</h3>",
        '<table class="matches">',
        "<tbody>",
    ]
    for match in round_.matches:
        player_a = _player_cell(tournament, match, match.player_a)
        player_b = _player_cell(tournament, match, match.player_b)
        result = f'<td class="result">{result_text(match)}</td>'
        lines.append(f"<tr>{player_a}{result}{player_b}</tr>")
    lines.extend(["</tbody>", "</table>"])
    if round_.byes:
        byes = ", ".join(_name(tournament, player_id) for player_id in round_.byes)
        lines.append(f'<p class="note">Bye: {byes}</p>')
    if any(_is_forfeit(match) for match in round_.matches):
        lines.append(f'<p class="note">{FORFEIT_KEY}</p>')
    return lines


def round_status(round_: Round) -> str:
    """Return "" for a finished round, else " (in progress)" or " (not played yet)"."""
    if round_.is_finished():
        return ""
    if any(match.result is not None for match in round_.matches):
        return " (in progress)"
    return " (not played yet)"


def result_text(match: Match) -> str:
    """Return "2 - 1", "vs" for no result, or "F - W" for a forfeit."""
    result = match.result
    if result is None:
        return "vs"
    if result.forfeited_by is None:
        return f"{result.score_a} - {result.score_b}"
    if result.forfeited_by == match.player_a:
        return "F - W"
    return "W - F"


def signed(number: int) -> str:
    """Return +3, -2, or 0."""
    return f"{number:+d}" if number else "0"


def _player_cell(tournament: Tournament, match: Match, player_id: PlayerId) -> str:
    """Return a table cell with the player's name, in bold for the winner."""
    css = ' class="winner"' if match.winner() == player_id else ""
    return f"<td{css}>{_name(tournament, player_id)}</td>"


def _is_forfeit(match: Match) -> bool:
    return match.result is not None and match.result.forfeited_by is not None


def _name(tournament: Tournament, player_id: PlayerId) -> str:
    """Return a player's name, escaped so it is shown as text (NFR-SE-2).

    Every name on the page comes through here.
    """
    return escape(tournament.player(player_id).name.text)
