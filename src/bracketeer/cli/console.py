"""Console input and output, plus the prompts every menu shares."""

import re
from collections.abc import Sequence

# Two whole numbers separated by a dash, a colon, or spaces: "2-1", "2 1".
SCORES = re.compile(r"([0-9]+)\s*[-:\s]\s*([0-9]+)")


class Console:
    """Reads what the organizer types and prints text.

    Every menu talks to the organizer through a Console, so the tests can pass
    in a scripted one instead of typing at a real keyboard.
    """

    def ask(self, prompt: str) -> str:
        """Show a prompt and return what was typed, without outer spaces."""
        return input(prompt).strip()

    def say(self, text: str = "") -> None:
        """Print a line of text."""
        print(text)


def heading(console: Console, title: str) -> None:
    """Print a title underlined with dashes, after a blank line."""
    console.say()
    console.say(title)
    console.say("-" * len(title))


def show_error(console: Console, error: Exception | str) -> None:
    """Print why an action was refused (NFR-US-2)."""
    console.say(f"Error: {error}")


def choose(console: Console, options: Sequence[str], back: str = "Back") -> int | None:
    """Show numbered options and return the index chosen, or None for 0."""
    for number, label in enumerate(options, start=1):
        console.say(f"  {number}. {label}")
    console.say(f"  0. {back}")
    while True:
        number = whole_number(console.ask("Choose: "))
        if number == 0:
            return None
        if number is not None and number <= len(options):
            return number - 1
        console.say(f"Type a number from 0 to {len(options)}.")


def ask_number(console: Console, prompt: str, low: int, high: int) -> int | None:
    """Ask for a whole number from low to high; Enter returns None."""
    while True:
        answer = console.ask(f"{prompt} ({low}-{high}, Enter to cancel): ")
        if not answer:
            return None
        number = whole_number(answer)
        if number is not None and low <= number <= high:
            return number
        console.say(f"Type a number from {low} to {high}, or press Enter to cancel.")


def ask_yes_no(console: Console, question: str) -> bool:
    """Ask a yes-or-no question until the answer is y or n."""
    while True:
        answer = console.ask(f"{question} (y/n): ").lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        console.say("Type y or n.")


def ask_rating(console: Console, prompt: str, if_empty: int | None) -> int | None:
    """Ask for a rating; Enter gives if_empty and "none" removes it.

    A negative number is passed on, so the domain's rule rejects it with its
    own message (R-PL-3).
    """
    while True:
        answer = console.ask(prompt)
        if not answer:
            return if_empty
        if answer.lower() == "none":
            return None
        try:
            return int(answer)
        except ValueError:
            console.say("A rating must be a whole number, such as 1500.")


def pause(console: Console) -> None:
    """Wait until the organizer presses Enter."""
    console.ask("Press Enter to go back.")


def whole_number(text: str) -> int | None:
    """Return text as a whole number of 0 or more, or None if it isn't one."""
    # isdigit() alone also accepts characters such as "²", which int() rejects.
    if text.isascii() and text.isdigit():
        return int(text)
    return None


def parse_scores(text: str) -> tuple[int, int] | None:
    """Return the two game scores in text such as "2-1", or None (R-RS-1)."""
    found = SCORES.fullmatch(text)
    if found is None:
        return None
    return int(found.group(1)), int(found.group(2))
