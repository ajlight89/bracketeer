# AI usage log

Bracketeer is being built with AI assistance via Claude by Anthropic. This log records what the AI provided, what I decided or changed myself, and how each piece was checked, so a reader can see which work is mine. Git holds the line-by-line history; this log records the decisions.

## How AI was used

- **Tool:** Claude (Anthropic), used as an assistant in a claude.ai Project that holds the abstract, the project plan, my environment notes and a progress file. One chat per phase.
- **Way of working:** work is done in small steps. For code, Claude provides complete code with an explanation and a verification command with the expected result. I enter the code into VS Code myself, run the checks, review and edit, and write the commits. Documents are drafted by Claude as Markdown files, and I review and edit them before committing.
- **Editor:** GitHub Copilot's inline suggestions are turned off in this repository's VS Code settings, so the code in the editor is code that was reviewed.
- **Decisions:** where Claude recommended a design choice, the log says so, along with the decision I made.
- **Per-change record:** each PR's _AI assistance_ section records the AI help for that change. This log is the summary.

## My rules for accepting AI output

1. **I can explain every line before I commit it.** If I can't, I ask until I can, or I don't use it.
2. **Nothing is accepted on trust.** Each step has a verification command with an expected result, and I compare the actual output.
3. **Version-sensitive facts are checked against official sources.** Tool versions, config keys and command-line flags change between releases.
4. **All code reaches `main` through a pull request.** `main` is protected, so there is no other route.
5. **No inline AI completions in the editor**, so all AI-written code passes through a chat where it is explained, and this log can be complete.
6. **AI never acts on the repository.** I run every command, create every Issue and PR, and do every merge.
7. **No secrets or personal data go into an AI tool.**
8. **AI-test experiment:** the one-shot AI test suite is generated in a separate chat that sees only `swiss.py`. My own tests are not tuned toward that comparison.

## Log

| Date                     | Work             | Claude provided                                                                                                                                                                                                                                                                                                                                | What I decided or changed                                                                                                                                                                                                   | Verified by                                                      |
| ------------------------ | ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| 2026-10-10 to 2026-10-17 | Foundation files | Drafts of the user stories (from my answers to an interview about organizers, players and spectators), the AI-feature requirements draft, the process model, ADR-0001 to ADR-0003, and the project configuration: `pyproject.toml`, the pinned dev dependencies, the CI and mutation-testing workflows, the PR template and the package layout | My decisions: the target users, three-letter tags instead of names on exports, no live sync, the organizer as the only user, the lightweight process, and which stories to keep. Reviewed each file before the first commit | Read each document against my interview answers and the abstract |

## How to add an entry

Add one row per working session, on the same day. Fill **What I decided or changed** honestly, including "no changes". When Claude's output was wrong, add a row that says what was wrong and how it was caught.
