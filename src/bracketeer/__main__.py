"""Start Bracketeer: python -m bracketeer, or Bracketeer.exe."""

import sys
from contextlib import suppress

from bracketeer.cli.menus import run


def main() -> int:
    """Run the app. An unexpected error is shown as a message, not a traceback."""
    try:
        return run()
    except Exception as error:
        print(f"Bracketeer hit an unexpected problem and has to close: {error}")
        # Keeps a double-clicked .exe's window open long enough to read it.
        with suppress(EOFError, KeyboardInterrupt):
            input("Press Enter to close.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
