"""Tests for the menus, driven by a scripted console."""

from bracketeer.app.session import TournamentSession, players_by_seed
from bracketeer.cli.menus import (
    matches_menu,
    players_menu,
    run,
    seeding_menu,
    start_tournament,
)


def names(players):
    return [player.name.text for player in players]


def test_a_round_robin_from_new_tournament_to_saved_and_exported(script, folder):
    console = script(
        "1", "Friday Smash Night", "2",  # new round robin
        "1", "1", "Ana", "1500", "Ben", "1800", "Cleo", "", "", "0",  # players
        "2", "1", "0",  # seed by rating
        "3", "y",  # start
        "1", "1", "1", "2-1", "0",  # enter a result
        "2", "",  # standings
        "4", "",  # export under the suggested name
        "5", "",  # save under the suggested name
        "0",  # quit
    )  # fmt: skip
    session = TournamentSession()
    assert run(console, session) == 0
    assert "Added Cleo." in console.screen
    assert "Recorded " in console.screen
    assert "Rank  Name" in console.screen
    saved = folder / "Friday Smash Night.bracketeer"
    assert f"Saved to {saved}." in console.screen
    assert console.lines[-1] == "Goodbye."
    assert saved.exists()
    assert (folder / "Friday Smash Night.html").exists()


def test_us_11_export_is_on_the_main_menu_only_after_the_start(script, league):
    console = script("0", "2")  # quit, discard the changes
    run(console, league)
    assert "Export as a web page" not in console.screen
    league.seed_by_rating()
    league.start()
    console = script("0", "2")
    run(console, league)
    assert "4. Export as a web page" in console.screen


def test_a_choice_that_isnt_on_the_menu_is_asked_again(script):
    console = script("9", "one", "0")
    run(console, TournamentSession())
    assert console.screen.count("Type a number from 0 to 2.") == 2


def test_ctrl_c_closes_the_app_without_a_traceback(script):
    class InterruptedConsole(script):
        def ask(self, prompt):
            raise KeyboardInterrupt

    console = InterruptedConsole()
    assert run(console, TournamentSession()) == 1
    assert console.lines[-1] == "Bracketeer was closed."


# Players (US-01, US-02)


def test_us_01_4_a_bad_rating_is_refused_with_a_message(script, league):
    console = script("1", "Dev", "abc", "1200", "Eve", "-5", "", "0")
    players_menu(console, league)
    assert "A rating must be a whole number, such as 1500." in console.screen
    assert (
        "Error: A rating must be a whole number of 0 or more; got -5." in console.screen
    )
    assert names(league.tournament.players) == ["Ana", "Ben", "Cleo", "Dev"]


def test_us_01_2_a_taken_name_is_refused_with_a_message(script, league):
    console = script("1", "ana", "", "", "0")
    players_menu(console, league)
    assert 'Error: The name "ana" is already taken.' in console.screen
    assert len(league.tournament.players) == 3


def test_us_02_1_edit_keeps_the_name_on_enter_and_none_clears_the_rating(
    script, league
):
    players_menu(script("2", "1", "", "none", "0"), league)
    ana = league.tournament.players[0]
    assert (ana.name.text, ana.rating) == ("Ana", None)


def test_us_02_2_removing_a_player_asks_first(script, league):
    console = script("3", "2", "n", "3", "2", "y", "0")
    players_menu(console, league)
    assert "Remove Ben? (y/n): n" in console.screen
    assert names(league.tournament.players) == ["Ana", "Cleo"]


def test_us_02_4_after_the_start_names_can_only_be_corrected(script, league):
    league.seed_by_rating()
    league.start()
    console = script("1", "1", "Anna", "0")
    players_menu(console, league)
    assert "Add players" not in console.screen
    assert names(league.tournament.players)[0] == "Anna"


# Seeding and starting (US-03)


def test_us_03_4_moving_a_player_to_seed_1_in_the_menu(script, league):
    seeding_menu(script("1", "3", "3", "1", "0"), league)
    assert names(players_by_seed(league.tournament)) == ["Cleo", "Ben", "Ana"]


def test_starting_asks_first(script, league):
    league.seed_by_rating()
    start_tournament(script("n"), league)
    assert not league.tournament.started
    start_tournament(script("y"), league)
    assert league.tournament.started


# Matches and results (US-04, US-07)


def test_us_07_4_scores_that_arent_whole_numbers_are_asked_again(script, cup):
    console = script("1", "1", "abc", "-1-2", "2-0", "0")
    matches_menu(console, cup)
    assert console.screen.count("Type two whole numbers of 0 or more") == 2
    assert "Recorded Ana 2 - 0 Dev." in console.screen


def test_us_07_3_a_draw_in_single_elimination_says_why_it_was_refused(script, cup):
    console = script("1", "1", "2-2", "0")
    matches_menu(console, cup)
    assert "Error: This format needs a winner in every match" in console.screen


def test_us_07_6_recording_a_forfeit(script, cup):
    console = script("1", "2", "f", "2", "0")  # match 2 is Ben v Cleo
    matches_menu(console, cup)
    match = cup.tournament.rounds[0].matches[1]
    assert match.result.forfeited_by == match.player_b
    assert "Recorded a forfeit by Cleo." in console.screen


def test_us_04_5_a_bracket_runs_to_its_champion(script, cup):
    console = script(
        "1", "1", "2-0",  # Ana beats Dev
        "1", "2", "2-1",  # Ben beats Cleo
        "3",  # generate the next round
        "1", "1", "0-3",  # Ben wins the final
        "0",
    )  # fmt: skip
    matches_menu(console, cup)
    assert "Every result is in. Generate the next round to go on." in console.screen
    assert "Round 2 is ready." in console.screen
    assert console.screen.endswith("Choose: 0")
    assert "The tournament is complete. Champion: Ben" in console.screen


def test_us_07_5_changing_a_locked_result_shows_why_it_was_refused(script, cup):
    console = script(
        "1", "1", "2-0", "1", "2", "2-1", "3",  # finish round 1, generate round 2
        "3",  # previous round
        "2", "1",  # clear match 1
        "0",
    )  # fmt: skip
    matches_menu(console, cup)
    assert "because the next round depends on it." in console.screen


def test_round_robin_has_no_generate_the_next_round_choice(script, league):
    league.seed_by_rating()
    league.start()
    console = script("0")
    matches_menu(console, league)
    assert "Generate the next round" not in console.screen


def test_round_robin_moves_through_its_planned_rounds(script):
    session = TournamentSession()
    session.new("League", "round_robin")
    for name in ["Ana", "Ben", "Cara", "Dev", "Eve", "Fay"]:
        session.add_player(name, None)
    session.seed_by_rating()
    session.start()
    console = script(
        "1", "1", "2-1", "1", "2", "2-0", "1", "3", "1-1",  # finish round 1
        "3",  # next round
        "4",  # previous round
        "0",
    )  # fmt: skip
    matches_menu(console, session)
    screen = console.screen
    assert "Round 1 of 5: 3 of 3 results" in screen
    assert "Every result in round 1 is in. Choose Next round to go on." in screen
    assert "Round 2 of 5: 0 of 3 results" in screen
    assert "Generate the next round" not in screen
    first, second = session.tournament.rounds[:2]
    pairs = [{m.player_a, m.player_b} for m in first.matches + second.matches]
    assert len(pairs) == 6 and all(pairs.count(pair) == 1 for pair in pairs)
    assert screen.rstrip().endswith("Choose: 0")
    assert screen.count("Round 1 of 5: 3 of 3 results") == 2  # back again
