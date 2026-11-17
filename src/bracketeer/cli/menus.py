"""The menus: the organizer picks each action by its number.

Every menu reads session.tournament to show it, and changes it only through
the session's methods. An ActionError from the session is shown as a message,
and the menu carries on (NFR-US-2).
"""

from collections.abc import Callable

from bracketeer.app.session import ActionError, TournamentSession, players_by_seed
from bracketeer.cli.console import (
    Console,
    ask_number,
    ask_rating,
    ask_yes_no,
    choose,
    heading,
    parse_scores,
    pause,
    show_error,
)
from bracketeer.cli.files import (
    export_web_page,
    new_tournament,
    ok_to_discard,
    open_tournament,
    save,
    save_as,
)
from bracketeer.cli.tables import (
    champion,
    current_round,
    fit,
    player_lines,
    plural,
    round_lines,
    standings_lines,
    status_lines,
)

Action = Callable[[Console, TournamentSession], object]

# Only single elimination plans rounds from results, one round at a time.
ADDS_ROUNDS_LATER = {"single_elimination"}


def run(
    console: Console | None = None, session: TournamentSession | None = None
) -> int:
    """Show the main menu until the organizer quits. Return the exit code."""
    console = console or Console()
    session = session or TournamentSession()
    console.say("Bracketeer: run small gaming tournaments")
    try:
        main_menu(console, session)
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C, or the input was closed: stop without a traceback.
        console.say()
        if session.has_unsaved_changes:
            console.say("Bracketeer was closed. The unsaved changes were lost.")
        else:
            console.say("Bracketeer was closed.")
        return 1
    console.say("Goodbye.")
    return 0


def main_menu(console: Console, session: TournamentSession) -> None:
    while True:
        tournament = session.tournament
        heading(console, "Bracketeer" if tournament is None else tournament.name)
        if tournament is not None:
            for line in status_lines(session):
                console.say(line)
        actions = main_actions(session)
        choice = choose(console, [label for label, _ in actions], back="Quit")
        if choice is None:
            if ok_to_discard(console, session):
                return
            continue
        attempt(console, session, actions[choice][1])


def main_actions(session: TournamentSession) -> list[tuple[str, Action]]:
    """Return the main menu's choices, which depend on the tournament's state."""
    tournament = session.tournament
    actions: list[tuple[str, Action]] = []
    if tournament is not None:
        if tournament.started:
            actions.append(("Matches and results", matches_menu))
            actions.append(("Standings", show_standings))
            actions.append(("Players", players_menu))
            actions.append(("Export as a web page", export_web_page))
        else:
            actions.append(("Players", players_menu))
            actions.append(("Seeding", seeding_menu))
            actions.append(("Start the tournament", start_tournament))
        actions.append(("Save", save))
        if session.path is not None:
            actions.append(("Save as", save_as))
    actions.append(("New tournament", new_tournament))
    actions.append(("Open a tournament", open_tournament))
    return actions


def attempt(console: Console, session: TournamentSession, action: Action) -> None:
    """Run an action; if the session refuses it, show why."""
    try:
        action(console, session)
    except ActionError as error:
        show_error(console, error)


# Players (US-01, US-02)


def players_menu(console: Console, session: TournamentSession) -> None:
    while True:
        players = session.tournament.players
        heading(console, f"Players ({len(players)})")
        show_players(console, players)
        if session.tournament.started:
            actions = [("Correct a name", rename_player)]
        else:
            actions = [
                ("Add players", add_players),
                ("Edit a player", edit_player),
                ("Remove a player", remove_player),
            ]
        choice = choose(console, [label for label, _ in actions])
        if choice is None:
            return
        attempt(console, session, actions[choice][1])


def show_players(console: Console, players) -> None:
    if not players:
        console.say("No players yet.")
        return
    for line in player_lines(players):
        console.say(line)


def add_players(console: Console, session: TournamentSession) -> None:
    """Add players one after another until the organizer presses Enter."""
    while True:
        name = console.ask("Name (Enter to stop): ")
        if not name:
            return
        rating = ask_rating(console, "Rating (Enter for none): ", None)
        try:
            session.add_player(name, rating)
        except ActionError as error:
            show_error(console, error)
            continue
        console.say(f"Added {name}.")


def edit_player(console: Console, session: TournamentSession) -> None:
    player = ask_player(console, session.tournament.players)
    if player is None:
        return
    old_name = player.name.text
    name = console.ask(f"Name (Enter keeps {old_name}): ") or old_name
    rating = "none" if player.rating is None else player.rating
    prompt = f"Rating (Enter keeps {rating}, or type none): "
    session.edit_player(player.id, name, ask_rating(console, prompt, player.rating))
    console.say(f"Updated {player.name.text}.")


def remove_player(console: Console, session: TournamentSession) -> None:
    player = ask_player(console, session.tournament.players)
    if player is None or not ask_yes_no(console, f"Remove {player.name.text}?"):
        return
    session.remove_player(player.id)
    console.say(f"Removed {player.name.text}.")


def rename_player(console: Console, session: TournamentSession) -> None:
    """Correct a name after the start; it changes everywhere (US-02 #3)."""
    player = ask_player(console, session.tournament.players)
    if player is None:
        return
    old_name = player.name.text
    name = console.ask("New name (Enter to cancel): ")
    if not name:
        return
    session.rename_player(player.id, name)
    console.say(f"Renamed {old_name} to {player.name.text}.")


def ask_player(console: Console, players):
    """Ask for a player by their number in the table shown; None if cancelled."""
    if not players:
        console.say("There are no players yet.")
        return None
    number = ask_number(console, "Player number", 1, len(players))
    return None if number is None else players[number - 1]


# Seeding (US-03)


def seeding_menu(console: Console, session: TournamentSession) -> None:
    actions = [
        ("Seed by rating (highest first, unrated last)", seed_by_rating),
        ("Seed randomly", seed_randomly),
        ("Move a player to a seed", move_to_seed),
    ]
    while True:
        heading(console, "Seeding")
        show_players(console, players_by_seed(session.tournament))
        choice = choose(console, [label for label, _ in actions])
        if choice is None:
            return
        attempt(console, session, actions[choice][1])


def seed_by_rating(console: Console, session: TournamentSession) -> None:
    session.seed_by_rating()
    console.say("Seeded by rating.")


def seed_randomly(console: Console, session: TournamentSession) -> None:
    session.seed_randomly()
    console.say("Seeded randomly.")


def move_to_seed(console: Console, session: TournamentSession) -> None:
    """Move one player to a seed; the others shift to make room (US-03 #4)."""
    players = players_by_seed(session.tournament)
    player = ask_player(console, players)
    if player is None:
        return
    seed = ask_number(console, f"New seed for {player.name.text}", 1, len(players))
    if seed is None:
        return
    session.move_to_seed(player.id, seed)
    console.say(f"{player.name.text} is now seed {seed}.")


def start_tournament(console: Console, session: TournamentSession) -> None:
    question = "Start the tournament? Players and seeds can't change after this."
    if not ask_yes_no(console, question):
        return
    session.start()
    matches = session.tournament.rounds[0].matches
    console.say(f"Started. Round 1 has {plural(len(matches), 'match')}.")


# Matches and results (US-04, US-05, US-07)


def matches_menu(console: Console, session: TournamentSession) -> None:
    """Show one round at a time; actions can switch to another round.

    Round robin plans every round at the start, so its later rounds already
    exist and Next round shows them. Single elimination adds each round once
    the one before it is finished, with Generate the next round.
    """
    tournament = session.tournament
    adds_rounds = tournament.format.key in ADDS_ROUNDS_LATER
    shown = current_round(tournament)
    while True:
        rounds = tournament.rounds
        is_last = shown.number == len(rounds)
        complete = tournament.is_complete()
        title = f"Round {shown.number}"
        if not adds_rounds:
            title += f" of {len(rounds)}"
        done = sum(match.result is not None for match in shown.matches)
        heading(console, f"{title}: {done} of {len(shown.matches)} results")
        for line in round_lines(tournament, shown):
            console.say(line)
        if complete:
            console.say(f"The tournament is complete. Champion: {champion(tournament)}")
        elif shown.is_finished() and not is_last:
            console.say(
                f"Every result in round {shown.number} is in. "
                "Choose Next round to go on."
            )
        elif adds_rounds and is_last and shown.is_finished():
            console.say("Every result is in. Generate the next round to go on.")

        actions = [("Enter a result", enter_result), ("Clear a result", clear_result)]
        if not is_last:
            actions.append(("Next round", next_round))
        if shown.number > 1:
            actions.append(("Previous round", previous_round))
        if adds_rounds and not complete:
            actions.append(("Generate the next round", generate_next_round))
        choice = choose(console, [label for label, _ in actions])
        if choice is None:
            return
        try:
            # An action returns the round to show next, or None to stay.
            shown = actions[choice][1](console, session, shown) or shown
        except ActionError as error:
            show_error(console, error)


def enter_result(console: Console, session: TournamentSession, round_) -> None:
    """Select the match, type the scores, press Enter (NFR-US-1)."""
    match = ask_match(console, round_)
    if match is None:
        return
    name_a, name_b = match_names(session, match)
    console.say(f"{fit(name_a, 38)} v {fit(name_b, 38)}")
    while True:
        answer = console.ask(
            "Scores in that order, like 2-1, or F for a forfeit (Enter to cancel): "
        )
        if not answer:
            return
        if answer.lower() == "f":
            record_forfeit(console, session, match)
            return
        scores = parse_scores(answer)
        if scores is not None:
            break
        console.say("Type two whole numbers of 0 or more, like 2-1, or F.")
    session.record_score(match.id, *scores)
    console.say(f"Recorded {name_a} {scores[0]} - {scores[1]} {name_b}.")


def record_forfeit(console: Console, session: TournamentSession, match) -> None:
    """Record a forfeit by whichever player didn't play (US-07 #6)."""
    names = match_names(session, match)
    console.say("Who forfeited?")
    choice = choose(console, names, back="Cancel")
    if choice is None:
        return
    forfeited_by = (match.player_a, match.player_b)[choice]
    session.record_forfeit(match.id, forfeited_by)
    console.say(f"Recorded a forfeit by {names[choice]}.")


def clear_result(console: Console, session: TournamentSession, round_) -> None:
    """Make a match unplayed again (US-07 #7)."""
    match = ask_match(console, round_)
    if match is None:
        return
    session.clear_result(match.id)
    console.say("Cleared the result.")


def next_round(console: Console, session: TournamentSession, round_):
    # Round numbers start at 1, so round n + 1 is at index n.
    return session.tournament.rounds[round_.number]


def previous_round(console: Console, session: TournamentSession, round_):
    return session.tournament.rounds[round_.number - 2]


def generate_next_round(console: Console, session: TournamentSession, round_):
    session.generate_next_round()
    new_round = session.tournament.rounds[-1]
    console.say(f"Round {new_round.number} is ready.")
    return new_round


def ask_match(console: Console, round_):
    """Ask for a match by its number in the round shown; None if cancelled."""
    number = ask_number(console, "Match number", 1, len(round_.matches))
    return None if number is None else round_.matches[number - 1]


def match_names(session: TournamentSession, match) -> list[str]:
    tournament = session.tournament
    return [
        tournament.player(match.player_a).name.text,
        tournament.player(match.player_b).name.text,
    ]


# Standings (US-09)


def show_standings(console: Console, session: TournamentSession) -> None:
    """Show the standings, worked out again from the results (US-09 #1)."""
    tournament = session.tournament
    heading(console, f"Standings: {tournament.name}")
    for line in standings_lines(tournament):
        console.say(line)
    if tournament.is_complete():
        console.say(f"The tournament is complete. Champion: {champion(tournament)}")
    pause(console)
