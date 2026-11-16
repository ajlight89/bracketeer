# Non-Functional Requirements

Non-functional requirements (NFRs) describe **how well** Bracketeer must work, rather than **what** it does. The [user stories](user-stories.md) cover what it does.

The NFRs are grouped by the quality characteristics of the ISO/IEC 25010 product quality model. Each one has a **fit criterion**: a measurement or check that decides whether it passes. A requirement like "the app should be fast" can't be tested; "every action responds within 1 second with 64 players" can.

**Reference machine:** the developer's Windows 11 computer. Timing checks use a 64-player tournament, the maximum allowed (R-PL-1 in [domain-rules.md](domain-rules.md)).

## Performance efficiency (PE)

| ID       | Requirement                                                                                                                         | How it's verified                                    |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| NFR-PE-1 | With 64 players, every action (starting, generating a round, entering a result, refreshing the standings) responds within 1 second. | Manual test checklist, using a 64-player demo file   |
| NFR-PE-2 | The `.exe` shows its main menu within 5 seconds of being opened.                                                                    | Manual check of each release build                   |

## Reliability (RE)

| ID       | Requirement                                                                                                                                                       | How it's verified                                         |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| NFR-RE-1 | Saving never leaves a half-written file. The new file is written in full first and only then replaces the old one, so a failed save keeps the previous version. | An automated test that makes a save fail partway through |
| NFR-RE-2 | Opening a damaged or unreadable file shows an error message, not a crash, and the file is never changed.                                                         | Automated tests that open truncated and invalid files     |
| NFR-RE-3 | Every saved file records its format version. A file with an unknown version is refused with a message.                                                           | An automated test that opens a file with a future version |
| NFR-RE-4 | Closing Bracketeer, starting a new tournament, or opening another file asks before discarding unsaved changes.                                                   | Automated menu tests; manual test checklist |

## Security (SE)

| ID       | Requirement                                                                                                                                                                                                                                                                                | How it's verified                                                   |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------- |
| NFR-SE-1 | **Trust assumption:** Bracketeer is a single-user application with no accounts. Whoever can use the computer is trusted, and protecting the saved files from other people is left to Windows (account password, screen lock, file permissions). Someone editing a saved file by hand is an accepted risk. | Documented here; the app treats every opened file as untrusted input (NFR-SE-4) |
| NFR-SE-2 | All user-entered text in an exported web page is escaped, so it is displayed as text and never run as code (cross-site scripting).                                                                                                                                                         | An automated test with a player named `<script>alert(1)</script>` (US-11 #3) |
| NFR-SE-3 | Bracketeer makes no network connections. All data stays on the computer.                                                                                                                                                                                                                   | Code review: no networking modules are imported in `src/`           |
| NFR-SE-4 | Opening a file never runs code from it. Files are read only as JSON data and every value is checked before use; Python's `pickle` and `eval` are never used on file contents.                                                                                                               | Code review; the tests for NFR-RE-2                                 |
| NFR-SE-5 | New files are written only inside the organizer's Bracketeer folder (`Documents\Bracketeer`), under a file name the organizer types or accepts. A name with a folder separator, a character Windows doesn't allow, or a name Windows reserves (such as `CON`) is refused, so a name can never point outside the folder. Saving a tournament that was opened from another folder writes back to that same file. An existing file is replaced only after the organizer confirms. | Automated tests of file names and the save prompt; manual test checklist |

## Interaction capability (usability) (US)

| ID       | Requirement                                                                                                        | How it's verified                                |
| -------- | ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------ |
| NFR-US-1 | A match result can be entered in three steps or fewer: select the match, type the scores, confirm.                 | Manual test checklist                            |
| NFR-US-2 | Every rejected input shows a message that says what's wrong and how to fix it. Users never see a Python traceback. | Acceptance criteria tests; manual test checklist |
| NFR-US-3 | Every menu and table fits in a terminal 80 characters wide (the usual default) without wrapping, even with 64 players and 40-character names. | An automated test of every table; manual test checklist |
| NFR-US-4 | Removing a player and overwriting a file ask for confirmation first.                                               | Automated menu tests; manual test checklist |

## Flexibility (portability) (PO)

| ID       | Requirement                                                                                                                                               | How it's verified                                                        |
| -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| NFR-PO-1 | The released `.exe` runs on 64-bit Windows 11 with no Python installed.                                                                                   | A manual check on a computer without Python before the release (US-12)   |
| NFR-PO-2 | The source code runs on Python 3.12 or later, and the automated tests also pass on Linux.                                                                 | GitHub Actions runs the tests on Ubuntu for every pull request           |
| NFR-PO-3 | An exported web page is a single, self-contained HTML file with no external files or web requests, and it displays correctly offline in Edge and Chrome. | An automated test that checks the file for external references; a manual check in both browsers |

## Maintainability (MA)

| ID       | Requirement                                                                                                                                  | How it's verified                                                   |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| NFR-MA-1 | The domain layer (`src/bracketeer/domain/`) imports only standard-library modules that do no input or output: no terminal, file, or network code. | An automated test that inspects the domain modules' imports         |
| NFR-MA-2 | Every testable acceptance criterion of a Must story is covered by an automated test that names the story and criterion (for example, `US-01 #2`). | Review of the test names against the story list before each release |
| NFR-MA-3 | `ruff check` and `ruff format --check` pass on every pull request.                                                                           | GitHub Actions                                                      |

NFR-SE-2 and NFR-PO-3 apply only if web export (US-11) is built.

## Sources

- ISO/IEC 25010 product quality model: https://iso25000.com/index.php/en/iso-25000-standards/iso-25010
- OWASP Cross Site Scripting Prevention Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html
- Python `pickle` security warning: https://docs.python.org/3/library/pickle.html
- Python `html.escape`: https://docs.python.org/3/library/html.html#html.escape
