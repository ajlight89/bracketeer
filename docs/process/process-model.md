# Process model: Bracketeer

_Owner: Aaron Light · Drafted with AI assistance (see `docs/ai/usage-log.md`)_

## 1. The model: lightweight Scrum ("Scrum-lite"), three two-week sprints

| Iteration | Dates | Phases | Goal | Tags |
|---|---|---|---|---|
| Setup | Sat Oct 17 | 1 | Repository, CI, board, requirements and first ADRs | `v0.1.0` |
| **Sprint 1** | Mon Oct 19 – Sun Nov 1 | 2–4 | Domain model; single elimination, round robin and Swiss; SQLite storage; undo | `v0.2.0`–`v0.4.0` |
| **Sprint 2** | Mon Nov 2 – Sun Nov 15 | 5–7 | GUI and exe; export and security; mutation testing and the AI-test experiment | `v0.5.0`–`v0.7.0` |
| **Sprint 3** | Mon Nov 16 – Sun Nov 29 | 8 | Wrap-up and `v1.0.0`, then buffer | `v1.0.0` |

## 2. Why this model

| Model | Fit for this project | Decision |
|---|---|---|
| **Waterfall** | All requirements first, then design, build and test in sequence. The deadline is fixed, the hardest part (Swiss pairing) is uncertain, and course topics such as testing, DevOps and security arrive one week at a time. Testing would happen in the last week, when it's too late to react. | Rejected |
| **Full Scrum** | Assumes a team: a separate Product Owner and Scrum Master, daily stand-ups, formal reviews. With one developer, those roles and meetings would be theatre. | Adapted |
| **Kanban** | Continuous flow suits one person, but with no timeboxes there's no natural point to review progress and adjust the plan. | Rejected, though the board uses Kanban-style columns |
| **Lightweight Scrum** | Keeps what pays off for a solo developer with a deadline: timeboxed sprints, an estimated backlog, a working and tagged increment each sprint, and a short review that feeds the next plan. Drops everything else. | **Chosen** |

It gives three things a waterfall can't: risk shows up early (Swiss is built in Sprint 1, not the last week), there's a working version at the end of every sprint, and each sprint's plan can use what the previous one showed.

## 3. Roles

| Role | Who | Responsibility |
|---|---|---|
| Product owner and developer | Aaron Light | Orders the backlog, builds, reviews, decides |
| AI assistant | Claude, in a claude.ai Project | Drafts code and documents and explains them. Every contribution is reviewed before it's committed and recorded in `docs/ai/usage-log.md`. |
| Customer stand-in | CPTR345 instructor | Represents the grading criteria; sees progress in class |

## 4. Sprint events

| Event | When | Output |
|---|---|---|
| Sprint planning (about 15 minutes) | First day of the sprint | Stories for the sprint get the sprint's Iteration on the board |
| Sprint review and retrospective, combined (about 30 minutes) | The sprint's last working session | The increment is tagged, and `docs/process/sprint-N.md` is written: one short paragraph on what was finished, the velocity, what went well, what didn't, and one change for the next sprint |

There's no daily meeting. The board is updated whenever a card changes state.

## 5. Board workflow

`Todo` → `In Progress` → `Done`.

- Move a card to **In Progress** when its branch is created.
- A card reaches **Done** only when the PR that finishes it is merged. Merging a PR with `Closes #N` closes the Issue and moves the card automatically.
- A story that's unfinished at the end of a sprint moves to the next sprint. Its points count in the sprint where it's finished.

## 6. Estimation and velocity

- **Story points go on `story` Issues only.** `docs`, `chore` and `bug` Issues are tracked on the board but not pointed, because they aren't features a user sees.
- **Scale:** Fibonacci (1, 2, 3, 5, 8, 13). The gaps grow because uncertainty grows with size. A 13 must be split.
- **Reference story:** US-02 *Register players* is 3 points. Other stories are estimated relative to it, not in hours.
- **Velocity** is the sum of the points of stories that are Done by the sprint's last day, read from the board's *Story Points* field sum. A story that's 90 % finished counts 0, so the number can't be inflated. It's recorded once, in the sprint note, and used to size the next sprint.

## 7. Definition of Done

### A story is Done when
1. Every acceptance criterion not marked (Should) is verified:
   - **[E] / [P]:** an automated test whose name contains the criterion ID (`test_us04_ac2_…`) passes in CI
   - **[CI]:** the named workflow step passes
   - **[M]:** the manual check, with its date and result, is written in the sprint note
2. CI is green on both runners.
3. Its code reached `main` through a merged PR.
4. Any decision it involved has an ADR, and the README is updated if behaviour a user sees changed.
5. AI help is recorded in the PR's *AI assistance* section and in the AI usage log.

### A pull request is ready to merge when
1. It closes or refers to its Issues (section 10). One PR may close several related Issues.
2. Its title is a Conventional Commit, because squash merge uses it as the commit message on `main`.
3. Both required checks are green: `Test (ubuntu-24.04)` and `Test (windows-latest)`.
4. The PR template is filled in, including **How verified** (what was run and what it showed) and **AI assistance**.
5. Review comments on the diff are optional. They're added when there's something worth recording: a question, a risk or a follow-up.

## 8. Batching work

- **Code:** one PR per story, or per small group of tightly related stories.
- **Documents:** one PR per group of related documents (for example the requirements, process model and first ADRs together).
- **ADRs:** written in the same PR as the code that makes the decision, on the day it's made. No separate Issue is needed.
- **Small fixes** (typos, config tweaks) are collected into one `chore:` PR, not one each.

## 9. Configuration management

- **Branches:** `type/N-slug`, for example `feat/12-single-elim` or `docs/3-requirements`. Short-lived; deleted on merge.
- **`main`** is protected: a PR is required, both checks must pass, the branch must be up to date, history is linear, the rules apply to admins, and force pushes and deletion are blocked.
- **Merging:** squash merge only, so `main` gets one Conventional Commit per PR.
- **Commit types:** `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `ci`, `build`, `chore`. A scope is optional, for example `docs(adr): …`.
- **Versions** follow Semantic Versioning 2.0.0. Before 1.0.0, the minor number goes up for each new increment and the patch number for fixes. A tag is made only on `main`, after CI is green.

Each phase ends with a tag: `v0.1.0` after Phase 1, `v0.2.0` after Phase 2, and so on to `v0.7.0`. Phase 8 ends with `v1.0.0`, the version handed in.

- **Dependencies:** `pyproject.toml` holds version ranges; `requirements-dev.txt` is the lock file that CI installs from. Upgrades go in a `chore:` PR.

## 10. `Closes` vs `Refs`, and the change loop

- **`Closes #N`** only when the PR meets every Done-when item of Issue #N. Write one `Closes` line per Issue.
- **`Refs #N`** when the PR is only one step toward the Issue.

An Issue closed early makes the board, and therefore velocity, wrong.

**The change loop** (every PR):
1. The work has an Issue with a Done-when list. It lands on the board automatically.
2. `git switch -c type/N-slug`, and move the card to In Progress.
3. Make the change and run its verification command.
4. Commit with a Conventional Commit message, and push.
5. `gh pr create`, with a `Closes` line for each Issue it finishes.
6. When both checks are green, tick the Done-when boxes on each Issue.
7. `gh pr merge --squash --delete-branch`, then `git pull` on `main`.

## 11. AI usage log

One row per working session, written the same day: what Claude provided, what I decided or changed, and how it was checked. Mistakes in AI output get their own row, because they feed the final report.

## 12. Scope priority

When time runs short, work is cut in this order, lowest first:

1. **Stretch goals:** double elimination.
2. **Anything not promised in the abstract** (listed in `plan.md`, section 2).
3. **Promised in the abstract:** never cut without the instructor's agreement.

## Change log
| Date | Change |
|---|---|
| 2026-10-17 | First version |
