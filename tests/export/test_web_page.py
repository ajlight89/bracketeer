"""Tests for the web page export (US-11, NFR-SE-2, NFR-PO-3)."""

from datetime import datetime
from html.parser import HTMLParser

import pytest

from bracketeer.domain.formats.round_robin import RoundRobin
from bracketeer.domain.formats.single_elimination import SingleElimination
from bracketeer.domain.tournament import Tournament
from bracketeer.domain.values import Result
from bracketeer.export.web_page import web_page, write_web_page

EXPORTED_AT = datetime(2026, 11, 20, 19, 5)

# Anything here would make the page load another file or reach the internet,
# or run code (NFR-PO-3, NFR-SE-2).
EXTERNAL = [
    "http:",
    "https:",
    "src=",
    "href=",
    "url(",
    "@import",
    "<link",
    "<script",
    "<img",
    "<iframe",
    "<object",
    "<embed",
]


class PageReader(HTMLParser):
    """Reads a page the way a browser does: which tags, and what text."""

    def __init__(self) -> None:
        super().__init__()  # convert_charrefs=True turns &lt; back into <
        self.tags: list[str] = []
        self.text: list[str] = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)

    def handle_data(self, data):
        self.text.append(data)


def read(page):
    reader = PageReader()
    reader.feed(page)
    reader.close()
    return reader


def cup(names=("Ana", "Ben", "Cleo", "Dev", "Eve", "Finn"), name="Cup Night"):
    """A started single elimination, seeded in registration order."""
    tournament = Tournament(name, SingleElimination())
    ids = [tournament.add_player(player) for player in names]
    tournament.seed_manually(ids)
    tournament.start()
    return tournament


@pytest.fixture
def league():
    """A 4-player round robin with a win, a draw, and a forfeit in round 1."""
    tournament = Tournament("Friday Smash Night", RoundRobin())
    for name in ["Ana", "Ben", "Cleo", "Dev"]:
        tournament.add_player(name)
    tournament.seed_by_rating()
    tournament.start()
    first, second = tournament.rounds[0].matches
    tournament.record_result(first.id, Result.played(2, 1))
    tournament.record_result(second.id, Result.forfeit(second.player_a))
    tournament.record_result(tournament.rounds[1].matches[0].id, Result.played(1, 1))
    return tournament


# What the page shows (US-11 #1)


def test_us_11_1_the_page_shows_the_rounds_results_and_standings(league):
    page = web_page(league, EXPORTED_AT)
    text = " ".join(read(page).text)
    assert "<h1>Friday Smash Night</h1>" in page
    assert "Round robin · 4 players · round 2 in progress" in text
    assert "<h2>Standings</h2>" in page
    for heading in ["Round 1", "Round 2 (in progress)", "Round 3 (not played yet)"]:
        assert f"<h3>{heading}</h3>" in page
    assert '<td class="result">2 - 1</td>' in page
    assert '<td class="result">1 - 1</td>' in page
    assert '<td class="result">vs</td>' in page
    assert "Exported from Bracketeer on 2026-11-20 at 19:05." in text


def test_the_winner_of_a_match_is_shown_in_bold(league):
    page = web_page(league, EXPORTED_AT)
    assert '<tr><td class="winner">Ana</td><td class="result">2 - 1</td>' in page


def test_a_forfeit_is_shown_with_its_key(league):
    page = web_page(league, EXPORTED_AT)
    assert '<td class="result">F - W</td>' in page
    assert "F forfeited, W won by forfeit" in page


def test_the_standings_list_every_player_once_with_a_signed_differential(league):
    page = web_page(league, EXPORTED_AT)
    table = page.split('<table class="standings">')[1].split("</table>")[0]
    rows = [line for line in table.splitlines() if line.startswith("<tr>")]
    assert len(rows) == 4
    assert rows[0] == (
        "<tr><td>1</td><td>Ana</td><td>2</td><td>1</td><td>1</td><td>0</td>"
        "<td>4</td><td>+1</td></tr>"
    )
    assert "P played, W won, D drawn, L lost" in page


def test_byes_are_listed_under_their_round():
    page = web_page(cup(), EXPORTED_AT)
    assert '<p class="note">Bye: Ana, Ben</p>' in page


def test_a_finished_bracket_names_its_champion():
    tournament = cup(names=("Ana", "Ben"))
    match = tournament.rounds[0].matches[0]
    tournament.record_result(match.id, Result.played(1, 3))
    page = web_page(tournament, EXPORTED_AT)
    assert '<p class="champion">Champion: Ben</p>' in page
    assert "Single elimination · 2 players · complete" in page


def test_a_bracket_waiting_for_its_next_round_says_so():
    tournament = cup(names=("Ana", "Ben", "Cleo", "Dev"))
    for match in tournament.rounds[0].matches:
        tournament.record_result(match.id, Result.played(2, 0))
    assert "waiting for round 2" in web_page(tournament, EXPORTED_AT)


def test_long_names_are_shown_in_full():
    long_name = "A" * 40
    page = web_page(cup(names=(long_name, "Ben")), EXPORTED_AT)
    assert f"<td>{long_name}</td>" in page


def test_a_tournament_that_hasnt_started_cant_be_exported():
    tournament = Tournament("Cup Night", SingleElimination())
    with pytest.raises(ValueError, match="started"):
        web_page(tournament, EXPORTED_AT)


# Safety and portability (US-11 #2 and #3, NFR-SE-2, NFR-PO-3)


def test_us_11_3_a_script_in_a_name_is_shown_as_text_and_never_run():
    attack = "<script>alert(1)</script>"
    tournament = cup(names=(attack, 'Tom & "Jerry"'), name="<b>Cup</b> Night")
    page = web_page(tournament, EXPORTED_AT)
    reader = read(page)
    assert "script" not in reader.tags
    assert "b" not in reader.tags
    assert attack in reader.text  # the browser shows the exact name as text
    assert 'Tom & "Jerry"' in reader.text
    assert "<b>Cup</b> Night" in reader.text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page


def test_us_11_2_the_page_is_one_file_with_no_external_references(league):
    page = web_page(league, EXPORTED_AT).lower()
    found = [text for text in EXTERNAL if text in page]
    assert not found, f"The page refers to something outside itself: {found}"


def test_the_page_is_a_complete_utf_8_document(league):
    page = web_page(league, EXPORTED_AT)
    assert page.startswith("<!DOCTYPE html>\n")
    assert '<meta charset="utf-8">' in page
    assert "<style>" in page
    assert page.endswith("</html>\n")


def test_write_web_page_saves_utf_8_whatever_the_computer_default(tmp_path):
    path = tmp_path / "cup.html"
    write_web_page(cup(names=("Zoë", "Ben")), path, EXPORTED_AT)
    assert "Zoë" in path.read_bytes().decode("utf-8")
