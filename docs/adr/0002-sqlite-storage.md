---
status: accepted
date: 2026-10-17
decision-makers: Aaron Light
consulted: Claude (AI assistant, drafted this record)
informed: CPTR345 instructor
---

# ADR-0002: Store tournament data locally in SQLite

## Context and Problem Statement

Bracketeer must keep tournaments between sessions (US-10) and must not lose a confirmed result if the app closes. Organizers use school or personal laptops, often without admin rights. The data includes minors' names, which shouldn't leave the machine. The app ships as one PyInstaller exe (US-13).

How should tournament data be stored?

## Decision Drivers

* No server, no accounts, works offline (A4)
* Atomic writes, so a crash can't leave half a result
* Integrity rules enforced by the store itself: unique player names, valid formats, foreign keys
* Nothing extra to install or bundle; the Python standard library preferred (US-13)
* The abstract promises parameterized SQL queries

## Considered Options

* One JSON file per tournament
* **SQLite through Python's built-in `sqlite3` module**
* A hosted database (for example PostgreSQL on a cloud provider, or Firebase)
* `pickle` or `shelve` files

## Decision Outcome

Chosen option: **SQLite through `sqlite3`**, because it is the only option that gives transactions and constraints with nothing to install, and keeps all data in one local file.

Details:

* **File location.** Windows: `%LOCALAPPDATA%\Bracketeer\bracketeer.db`, which is inside the user's own profile, so it needs no admin rights. Other systems: `~/.bracketeer/bracketeer.db`. The environment variable `BRACKETEER_DB` overrides the path, for demos and manual tests. Automated tests use `:memory:` or pytest's `tmp_path` and never touch the real file.
* **Access** only through `SqliteTournamentRepository` (ADR-0003; the Repository pattern is ADR-0005). Every query uses `?` placeholders.
* **Each connection** runs `PRAGMA foreign_keys = ON`. SQLite leaves foreign-key enforcement off by default.
* **Tables are declared `STRICT`**, so a value of the wrong type is rejected instead of silently stored.
* **Every user action** that changes data runs in one transaction, which is committed before the service reports success.
* **Schema versions** are tracked with `PRAGMA user_version`, so a later release could migrate an existing database.
* **Timestamps** are stored as ISO-8601 text in UTC.

### Consequences

* Good, because transactions make every result entry all-or-nothing.
* Good, because `UNIQUE`, `CHECK` and `REFERENCES` constraints catch bugs that would otherwise corrupt data.
* Good, because one file is easy to back up, and DB Browser for SQLite can inspect it during development.
* Good, because `sqlite3` is in the standard library, so the exe has no extra dependency.
* Bad, because schema changes after 1.0 need migration code.
* Bad, because only one process can write at a time. That's acceptable for a single-user desktop app.
* Bad, because of a **version trap**:
  * Python's built-in SQLite on the development machine is **3.49.1**, but the `sqlite3` command-line tool is **3.53.4**. A query that works in the CLI can fail from Python, so SQL is always tried from Python, never only in the CLI.
  * The exe bundles the SQLite library of whichever Python the `windows-latest` release runner installs, which may differ again.
  * The code targets features available in **3.37.0**, the version that introduced `STRICT` tables, and a test enforces that minimum.

### Confirmation

* `tests/unit/test_sqlite_version.py` asserts `sqlite3.sqlite_version_info >= (3, 37, 0)` on both CI runners.
* The repository contract tests run against both the SQLite and the in-memory repository (ADR-0005).
* bandit rule B608 and the hostile-name test from US-10-AC2 guard against string-built SQL.

## Pros and Cons of the Options

### JSON file per tournament
* Good, because it's human-readable and in the standard library.
* Bad, because it has no transactions: a crash while writing can corrupt the file, unless we write our own atomic-replace logic.
* Bad, because it has no constraints, so every integrity rule has to be written in Python.
* Bad, because it wouldn't demonstrate parameterized SQL, which the course expects.

### SQLite via `sqlite3`
* Good, because it's ACID, has constraints, is one file, and is in the standard library.
* Bad, because it needs schema migrations and has the version differences described above.

### Hosted database
* Good, because it would allow live sync and multiple devices.
* Bad, because it needs a server, accounts and a network connection, and it would put minors' data on a third-party service. Live sync is out of scope (A5).

### pickle / shelve
* Good, because it's the least code.
* Bad, because loading a pickle can run arbitrary code, so a tampered file becomes a security hole. It also has no queries and no constraints.

## More Information

* Python `sqlite3` documentation: https://docs.python.org/3/library/sqlite3.html
* SQLite STRICT tables: https://www.sqlite.org/stricttables.html
* OWASP Query Parameterization Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Query_Parameterization_Cheat_Sheet.html
