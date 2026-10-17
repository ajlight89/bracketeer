---
status: accepted
date: 2026-10-17
decision-makers: Aaron Light
consulted: Claude (AI assistant, drafted this record)
informed: CPTR345 instructor
---

# ADR-0001: Record architecture decisions as MADR files in the repo

## Context and Problem Statement

Bracketeer will make about a dozen significant design decisions: storage, layering, the format, repository and command patterns, HTML escaping, and more. Later work depends on remembering not just *what* was decided but *why*, and what was rejected. The Phase 5 change request and the final report both need that reasoning, and the course grades it.

Where and how should decisions be recorded so that the reasoning survives and its date can be shown?

## Decision Drivers

* The reasoning must be recorded **the day the decision is made**. Records written long after the decision show up as such in the commit history.
* The rejected options and their trade-offs must be visible, not just the winner.
* Records should live next to the code, go through the same PRs, and need no extra tools.
* A decision that changes must stay traceable: what replaced it, and why.

## Considered Options

* No formal records; reasoning in commit messages and PR descriptions
* One design document, updated in place
* A wiki (GitHub Wiki)
* Architecture decision records in the Michael Nygard format
* **Architecture decision records using the MADR template, in `docs/adr/`**

## Decision Outcome

Chosen option: **MADR records in `docs/adr/`**, because it is the only option that captures considered options with pros and cons in a fixed structure, sits next to the code, and is reviewed in a PR like any other change.

Rules:
1. One decision per file, named `NNNN-short-title.md` and numbered in order.
2. Written on the day the decision is made, in the same PR as the work that makes the decision. A decision made before any code exists (such as ADRs 0002 and 0003) goes in a `docs:` PR.
3. Once an ADR is **accepted**, it isn't rewritten. If the decision changes, a new ADR supersedes it, and the old one's status becomes `superseded by ADR-NNNN`.
4. `docs/adr/README.md` lists every ADR with its status and date.
5. When a decision was made before it was written down, the record says so and gives both dates.

### Consequences

* Good, because each decision's reasoning, alternatives and date can be found in one place, and its Git history proves when it was written.
* Good, because the design doc (Phase 6) can link to ADRs instead of repeating them.
* Bad, because each ADR takes about 20 minutes to write, so only significant decisions get one.
* Neutral: there is a risk of over-recording. Only decisions that are hard to reverse, or that a grader would ask "why?" about, get an ADR.

### Confirmation

* `docs/adr/README.md` lists every ADR file. Checked at each sprint review.
* Each ADR's front-matter date matches the date of the PR that added it.
* At least one ADR for each pattern named in the abstract (Strategy, Repository, Command).

## Pros and Cons of the Options

### No formal records
* Good, because it costs nothing.
* Bad, because commit messages are short, and the rejected options are lost.

### One design document
* Good, because everything is in one place.
* Bad, because updating in place erases the history of when, and why, a decision changed.

### GitHub Wiki
* Good, because it's easy to edit.
* Bad, because the wiki is a separate repository with no PR review and no link to the code version.

### Nygard-format ADRs
* Good, because the format is short: context, decision, consequences.
* Bad, because it has no explicit section for considered options and their pros and cons, which is the part graders look for.

### MADR ADRs
* Good, because the template requires options, drivers, consequences and confirmation.
* Good, because it's Markdown, renders on GitHub and goes through PRs.
* Bad, because it's longer to write than a Nygard record.

## More Information

* MADR template: https://adr.github.io/madr/
* ADR overview and anti-patterns: https://adr.github.io/
