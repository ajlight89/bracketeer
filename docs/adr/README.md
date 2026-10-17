# Architecture decision records

Each significant design decision is recorded here using the [MADR](https://adr.github.io/madr/) template, on the day it is made (see ADR-0001). An accepted ADR isn't rewritten. If the decision changes, a new ADR supersedes it.

| ADR | Title | Status | Date |
|---|---|---|---|
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions as MADR files in the repo | Accepted | 2026-10-17 |
| [0002](0002-sqlite-storage.md) | Store tournament data locally in SQLite | Accepted | 2026-10-17 |
| [0003](0003-layered-architecture.md) | Layered architecture with a services layer | Accepted | 2026-10-17 |

Planned: 0004 FormatStrategy (Phase 2), 0005 Repository with an in-memory fake and 0006 Command for undoable result entry (Phase 4), 0007 Jinja2 with autoescape for the HTML export (Phase 6).
