# Bracketeer

[![CI](https://github.com/ajlight89/bracketeer/actions/workflows/ci.yml/badge.svg)](https://github.com/ajlight89/bracketeer/actions/workflows/ci.yml)

A Windows desktop tournament manager for game nights and small esports events: single elimination,
round robin and Swiss pairing, live standings with tiebreakers, undoable score entry, and an HTML
results export for GitHub Pages.

CPTR345 Software Engineering final project, Fall 2026. Status: in development.

## Development setup (Windows, PowerShell 7, Python 3.12)

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pip install -e . --no-deps
pytest
```

## Documentation

- [User stories](docs/requirements/user-stories.md)
- [AI-suggested seeding (future feature)](docs/requirements/ai-feature.md)
- [Process model](docs/process/process-model.md)
- [Architecture decision records](docs/adr/README.md)
- [AI usage log](docs/ai/usage-log.md)
