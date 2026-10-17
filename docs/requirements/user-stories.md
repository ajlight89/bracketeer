# User stories: Bracketeer

_Owner: Aaron Light · Drafted with AI assistance (see `docs/ai/usage-log.md`)_

## 1. Vision

> **For** teachers, coaches and community organizers **who** run small gaming tournaments with pen and paper,
> **Bracketeer is** a lightweight Windows app **that** runs a single-elimination, round-robin or Swiss event from sign-up to final standings on one laptop.
> **Unlike** online bracket platforms, it needs no accounts, keeps players' data on the organizer's own machine, and publishes results with privacy-safe three-letter tags by default.

(Positioning template from Geoffrey Moore, *Crossing the Chasm*.)

## 2. Stakeholders

| Stakeholder | Who | What they need | How they meet the product |
|---|---|---|---|
| **Organizer** (primary user) | School esports coaches and teachers; members of the public hosting at a rec center or similar | Fast setup, correct pairings, recovery from typing mistakes, standings people trust | Uses the app |
| **Player** | Students (often minors) and adult rec players; an entrant may be a team | Fair pairings, knowing their next match, privacy | Sees the projected screen and the published page; never uses the app |
| **Spectator** | Parents, classmates, friends | Follow results after the event or between rounds | Reads the published page, usually on a phone |
| **School or venue** | School administration and IT, rec-center staff | Minors' privacy; runs on laptops without admin rights | Approves use |
| **Instructor** | CPTR345 instructor | Evidence of software engineering practice | Grades the repository and report |

## 3. Personas

These personas are invented, not based on interviews.

- **Ms. Rivera, high-school esports coach.** Runs a 16-player club night every other Friday on a school laptop. Today she draws the bracket on a whiteboard and keeps standings in a notebook. She can't install software that needs admin rights, and she must not post students' full names online.
- **Sam, rec-center game-night host.** Runs a monthly Swiss night for 6–20 adults on his own laptop. He wants standings that people trust and a link to share afterwards.

## 4. Scope

### Assumptions
- **A1** An entrant is one named player or team. There is no roster management.
- **A2** Results are recorded as games won (for example 3–1). There are no draws.
- **A3** The organizer is the only person who uses the app.
- **A4** The app runs on one laptop. Only publishing needs an internet connection.
- **A5** Spectators see results after the event or between rounds. Nothing syncs live.
- **A6** A tournament has 2–64 entrants.

### Out of scope
| Item | Why |
|---|---|
| A player-facing app or web interface | Needs a server and a web UI |
| Live sync of results | Static pages are enough for these events (A5) |
| Accounts, logins, online registration | Data stays on the organizer's laptop |
| Team rosters, draws | A1, A2 |
| Full names on the public page | Players' privacy, many of them minors (US-12) |
| Double elimination | Stretch goal only |

## 5. Conventions

- Each story reads "As a … I want … so that …".
- **Acceptance criteria** use Given/When/Then and have IDs of the form `US-NN-ACn`. A test for a criterion includes the ID in its name, for example `test_us04_ac2_five_players_get_three_byes`.
- **Verification tag** on each criterion: **[E]** example-based pytest test; **[P]** Hypothesis property test; **[CI]** checked by a GitHub Actions job; **[M]** manual check, recorded in the sprint note.
- Criteria describe behaviour, not widgets, so most are tested at the service layer. A story finished before the GUI exists is Done when its criteria pass at the service layer.
- **Points** use the Fibonacci scale (1, 2, 3, 5, 8, 13). The reference story is US-02 at 3 points.

## 6. Summary

| ID | Story | Who | Priority | Points | Sprint |
|---|---|---|---|---|---|
| US-01 | Create a tournament | Organizer | Must | 2 | 1 |
| US-02 | Register players | Organizer | Must | 3 | 1 |
| US-03 | Seed players | Organizer | Must | 3 | 1 |
| US-04 | Generate a single-elimination bracket | Organizer | Must | 8 | 1 |
| US-05 | Run a round-robin event | Organizer | Must | 5 | 1 |
| US-06 | Run a Swiss event | Organizer | Must | 8 | 1 |
| US-07 | Enter a match result | Organizer | Must | 3 | 1 |
| US-08 | Undo a mistaken result | Organizer | Must | 5 | 1 |
| US-09 | View live standings | Organizer | Must | 3 | 1 |
| US-10 | Resume an event after closing the app | Organizer | Must | 5 | 1 |
| US-11 | Export a safe results page | Organizer | Must | 5 | 2 |
| US-12 | Show tags instead of names by default | Organizer | Must | 3 | 2 |
| US-13 | Install from a Release download | Organizer | Must | 3 | 2 |
| US-14 | Follow results on my phone | Spectator | Must | 3 | 2 |

**Planned points:** Sprint 1 = 45, Sprint 2 = 14, total 59. Sprint 1 holds all the tournament logic. Sprint 2 also carries work that isn't pointed because it isn't a user story: the threat model, the CI security checks, mutation testing and the AI-test experiment.

Format-specific tiebreakers belong to the format stories (US-05, US-06). US-09 covers only the rules every format shares.

---

## 7. Stories

### US-01 Create a tournament
**As an** organizer, **I want** to create a tournament with a name and a format, **so that** I can set up an event in one place.
Priority: Must · Points: 2 · Sprint: 1

- **US-01-AC1 [E]** Given no tournaments exist, when I create "Friday Smash" as a Swiss tournament, then it is listed with format Swiss and status Setup.
- **US-01-AC2 [E]** Given the create form, when I submit a name that is empty, whitespace only, or longer than 80 characters, then it is rejected with a message saying why.
- **US-01-AC3 [E]** Given a tournament in Setup, when I change its format, then the change is saved. Given a tournament that has started, when I try to change its format, then the change is rejected.

### US-02 Register players
**As an** organizer, **I want** to add and remove players before the event starts, **so that** the entrant list matches who actually showed up.
Priority: Must · Points: 3 (reference story) · Sprint: 1

- **US-02-AC1 [E]** Given a tournament in Setup, when I add "Jordan Avery", then the player is listed with the next free seed.
- **US-02-AC2 [E]** Given "Jordan Avery" is registered, when I add "jordan avery " (different case, trailing space), then it is rejected as a duplicate.
- **US-02-AC3 [E]** Given a name that is empty after trimming or longer than 40 characters, or a 65th player (A6), when I add it, then it is rejected with a message.
- **US-02-AC4 [E]** Given a tournament that has started, when I add or remove a player, then it is rejected and the list is unchanged.

### US-03 Seed players
**As an** organizer, **I want** to set the seed order by hand or randomly, **so that** strong players don't meet in the first round.
Priority: Must · Points: 3 · Sprint: 1

- **US-03-AC1 [E]** Given players registered in the order A, B, C, then their seeds are 1, 2, 3.
- **US-03-AC2 [P]** Given any list of players, when I move a player to a new position, then the seeds are always a permutation of 1..n, with no gaps and no duplicates.
- **US-03-AC3 [P]** Given any list of players, when I randomize the seeds, then the result is a permutation of 1..n, and the same random seed always gives the same order.
- **US-03-AC4 [E]** Given a tournament that has started, when I change seeds, then it is rejected.

### US-04 Generate a single-elimination bracket
**As an** organizer, **I want** Bracketeer to build a seeded single-elimination bracket with byes, **so that** I don't have to work out the pairings by hand.
Priority: Must · Points: 8 · Sprint: 1

- **US-04-AC1 [E]** Given 8 players seeded 1–8, when I start the tournament, then round 1 is 1 v 8, 4 v 5, 2 v 7, 3 v 6, in that order.
- **US-04-AC2 [E]** Given 5 players, when I start, then seeds 1, 2 and 3 get byes, advance to round 2 automatically, and the only real round-1 match is 4 v 5.
- **US-04-AC3 [P]** Given n players (2 ≤ n ≤ 64), when every match has been played, then exactly n − 1 real matches were played and there is exactly one champion, who never lost.
- **US-04-AC4 [P]** Given the higher seed wins every match, then seeds 1 and 2 meet only in the final.

### US-05 Run a round-robin event
**As an** organizer, **I want** everyone to play everyone, with fair tiebreakers, **so that** small groups get the most games and a trusted ranking.
Priority: Must · Points: 5 · Sprint: 1

- **US-05-AC1 [E]** Given 6 players, when I start, then there are 5 rounds of 3 matches.
- **US-05-AC2 [P]** Given n players (2–64), then every pair meets exactly once and no player appears twice in a round.
- **US-05-AC3 [P]** Given an odd n, then there are n rounds and each player has exactly one bye.
- **US-05-AC4 [E]** Given players tied on wins, then head-to-head decides first, then game differential (games won minus games lost), then the better seed.

### US-06 Run a Swiss event
**As an** organizer, **I want** players with similar records to meet each round, without rematches, **so that** a large group gets a fair ranking in only a few rounds.
Priority: Must · Points: 8 · Sprint: 1 (pairing work time-boxed to 3 hours)

- **US-06-AC1 [E]** Given 8 players, then the default number of rounds is 3 (⌈log₂ n⌉), and before starting I can choose any number from 1 to n − 1.
- **US-06-AC2 [E]** Given 8 players seeded 1–8, then round 1 is 1 v 5, 2 v 6, 3 v 7, 4 v 8 (top half against bottom half).
- **US-06-AC3 [P]** Given any results so far, when I generate the next round, then players are paired within score groups and no pair meets twice whenever a rematch-free pairing exists. For n ≤ 8 this is checked against a brute-force search.
- **US-06-AC4 [P]** Given an odd n, then each round's bye goes to the lowest-ranked player who hasn't had one, a bye counts as a win, and no player gets two byes.
- **US-06-AC5 [E]** Given players tied on points, then the higher Buchholz score (the sum of their opponents' points) ranks higher, and after that the better seed.

### US-07 Enter a match result
**As an** organizer, **I want** to type in each match's score as it finishes, **so that** the event keeps moving and standings stay current.
Priority: Must · Points: 3 · Sprint: 1

- **US-07-AC1 [E]** Given a real match in the current round, when I enter 3–1, then the match is reported with player 1 as the winner.
- **US-07-AC2 [E]** Given I enter equal scores such as 2–2, then the result is rejected, because draws aren't supported (A2).
- **US-07-AC3 [E]** Given I enter a negative score, a non-whole number, or a score above 99, then the result is rejected.
- **US-07-AC4 [E]** Given a bye, when I try to enter a score for it, then it is rejected.

### US-08 Undo a mistaken result
**As an** organizer, **I want** to undo the last results I entered, **so that** a typo doesn't ruin the standings.
Priority: Must · Points: 5 · Sprint: 1

- **US-08-AC1 [P]** Given any tournament state, when I report a result and then undo it, then the tournament is exactly as it was before.
- **US-08-AC2 [E]** Given I reported M1 and then M2, when I undo twice, then M2 and then M1 become unreported, in that order.
- **US-08-AC3 [E]** Given there's nothing to undo in the current round (including after the next round was generated), when I undo, then nothing changes and I'm told why.
- **US-08-AC4 [M]** Given the round view has focus, when I press Ctrl+Z, then the last result is undone.

### US-09 View live standings
**As an** organizer, **I want** standings that update after every result, **so that** I can announce who's leading at any time.
Priority: Must · Points: 3 · Sprint: 1

- **US-09-AC1 [P]** Given any tournament state in any format, then the standings list every player exactly once, ranked 1..n.
- **US-09-AC2 [P]** Given the same tournament state, then the standings are identical every time they're computed; ties always fall back to seed.
- **US-09-AC3 [E]** Given a single-elimination event, then players are ranked by the round they reached, champion first, with ties broken by seed.

_The same AC1 and AC2 property tests run against every format, which shows the formats are interchangeable._

### US-10 Resume an event after closing the app
**As an** organizer, **I want** my tournaments to be saved automatically, **so that** closing the laptop doesn't lose the event.
Priority: Must · Points: 5 · Sprint: 1

- **US-10-AC1 [E]** Given an in-progress tournament, when I close and reopen Bracketeer, then it is listed, and opening it restores the players, seeds, rounds, results and standings exactly.
- **US-10-AC2 [E]** Given a player named `Robert'); DROP TABLE player;--`, when the tournament is saved and reloaded, then the name comes back unchanged and every table is intact.

### US-11 Export a safe results page
**As an** organizer, **I want** to export the bracket and standings as one web page, **so that** I can share results without anyone touching my laptop.
Priority: Must · Points: 5 · Sprint: 2

- **US-11-AC1 [E]** Given a tournament in progress or finished, when I export, then one self-contained `.html` file is written with every round's matches and the current standings. It has inline CSS, no scripts and no external requests.
- **US-11-AC2 [E]** Given a tournament named `<img src=x onerror=alert(1)>`, and a player shown as `<script>alert(1)</script>` (in "first name + last initial" mode), when I export, then both appear as literal text, and the file contains no `<script` or `<img` tag.
- **US-11-AC3 [E]** Given I export again after another round, then the file reflects the new state and shows the round number and the export time.
- **US-11-AC4 [M]** Given the exported file, when I open it in a browser with no network connection, then it displays correctly.

### US-12 Show tags instead of names by default
**As an** organizer working with minors, **I want** exports to show short tags unless I deliberately choose otherwise, **so that** players' names don't end up on a public website.
Priority: Must · Points: 3 · Sprint: 2

- **US-12-AC1 [E]** Given new players "Jordan Avery", "Ninja" and "Al", then their default tags are JAV, NIN and AL (bowling-alley style).
- **US-12-AC2 [E]** Given I edit a tag, then it must be 1–3 characters from A–Z and 0–9 and unique within the tournament, or it is rejected.
- **US-12-AC3 [P]** Given any list of players, then the default tags are unique within the tournament. A clash gets the next free variant, for example JA2.
- **US-12-AC4 [E]** Given the default export setting, when I export, then the file contains each player's tag and none of their registered names. Choosing "first name + last initial" first requires confirming that the players or their parents consented, and then shows "Jordan Avery" as "Jordan A.".

_Default tag rule:_ keep the name's letters and digits (accents removed, uppercased, split into words). One word: its first three characters. Two or more words: the first character of the first word and the first two of the last. If the tag is taken, replace its last character with 2, 3, … until it's free. A name with no letters or digits gets `P` plus the player's seed.

### US-13 Install from a Release download
**As an** organizer on a school laptop, **I want** to download and run Bracketeer without installing Python or having admin rights, **so that** I can use the machine I already have.
Priority: Must · Points: 3 · Sprint: 2

- **US-13-AC1 [M]** Given a Windows 10 or 11 PC without Python and without admin rights, when I download `Bracketeer.exe` from the latest GitHub Release and run it, then the app opens and I can create a tournament.
- **US-13-AC2 [CI]** Given a `v*` tag is pushed, then CI builds the exe on `windows-latest` and attaches it to that Release.
- **US-13-AC3 [M]** Given the Release page, then it explains that the exe is unsigned, that Windows SmartScreen may warn, and how to run it anyway.

### US-14 Follow results on my phone
**As a** spectator, **I want** to open the published results on my phone, **so that** I can follow the event without being there.
Priority: Must · Points: 3 · Sprint: 2

- **US-14-AC1 [M]** Given the organizer has published an export to GitHub Pages, when I open the URL, then I see the latest exported rounds and standings.
- **US-14-AC2 [M]** Given a screen 360 px wide, then the page itself doesn't scroll sideways; wide tables scroll inside their own box.
- **US-14-AC3 [E]** Given the page, then it states the round, the export time, and that results aren't live (A5).
- **US-14-AC4 [M]** Given the README, then it has step-by-step instructions for publishing an export to GitHub Pages.

---

## 8. Glossary

| Term | Meaning |
|---|---|
| Entrant / player | One named competitor in a tournament; may be a team name (A1) |
| Seed | A player's starting rank: 1 is the strongest expected player |
| Bye | A round in which a player has no opponent. It counts as a win and has no score |
| Real match | A match between two players, as opposed to a bye |
| Score group | Swiss: the players on the same number of points |
| Buchholz | Swiss tiebreaker: the sum of a player's opponents' points (a bye adds 0) |
| Game differential | Round-robin tiebreaker: games won minus games lost |
| Display tag | The 1–3 character label used on exports by default (US-12) |
