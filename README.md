# Bracketeer

A Windows terminal app for organizing and running small gaming tournaments, such
as a game night or a school esports event. Register and seed players, run a round
robin or single elimination tournament, enter results, and follow the standings.
Tournaments are saved as files on your computer, so Bracketeer needs no server
and no internet connection.

Final project for CPTR 345 Software Engineering, Fall 2026.

> **Status:** in development. The first release is planned for late November 2026.

## Features (v1.0)

- A menu-driven terminal interface: choose an action by its number
- Add, edit, and remove players, with an optional rating
- Seed players manually, at random, or by rating
- Round robin and single elimination formats
- Record match results, including forfeits
- Standings with tiebreakers
- Save a tournament to a file and open it again
- A single Windows `.exe`, so Python doesn't need to be installed

## Documentation

The requirements are the heart of the project. A suggested reading order:

1. [User stories](docs/requirements/user-stories.md): what an organizer can do,
   with acceptance criteria
2. [Domain rules](docs/requirements/domain-rules.md): the tournament rules the
   stories rely on
3. [Non-functional requirements](docs/requirements/non-functional.md): how well
   the app must work, and how each requirement is checked
4. [AI Smart Seeding proposal](docs/requirements/ai-smart-seeding.md): requirements
   for a possible future AI feature
5. [Design](docs/design.md): the class diagram, layers, and design patterns
6. [Key decisions](docs/key-decisions.md): the main decisions and scope changes,
   and why they were made

## Running from source

Requires Python 3.12 on Windows.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Then start Bracketeer:

```powershell
python -m bracketeer
```

Choose each action by typing its number and pressing Enter. Tournaments are saved
as `.bracketeer` files in a `Bracketeer` folder in your Documents, and Open lists
them for you to choose from.

## Running the tests

With the virtual environment active:

```powershell
pytest
ruff check .
ruff format --check .
```

GitHub Actions runs the same checks on every pull request.

## How the project is run

- Each user story is a GitHub issue, with its acceptance criteria as a checklist.
- Work happens on a short-lived branch per feature and is merged through a pull
  request that closes its issue.
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/),
  and releases follow [Semantic Versioning](https://semver.org/).
- Progress is tracked on the project board and in three milestones: Domain
  complete, Working app, and Delivery.
