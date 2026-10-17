# AI feature requirements: suggested seeding

_Owner: Aaron Light · **Status: DRAFT. Future feature, not part of this version.** A light final edit (failure modes, override, fairness to new players) comes at the end of the project. Drafted with AI assistance (see `docs/ai/usage-log.md`)._

## 1. Summary

When an organizer seeds a new event, Bracketeer can **suggest** a seed order based on how the same entrants did in earlier Bracketeer tournaments on the same computer. The organizer sees the reasoning for each suggestion and decides whether to apply it. The feature **augments** the organizer's judgement and never replaces it: nothing is applied automatically.

This document follows the structure of Google's People + AI Guidebook (PAIR) and checks the design against Microsoft's Guidelines for Human-AI Interaction (HAX).

## 2. User need and defining success (PAIR: *User Needs + Defining Success*)

### 2.1 The problem
- Seeding by hand is slow, and it is unreliable when the organizer doesn't know every player's level. Ms. Rivera has 16 students and changes membership each term.
- Bad seeding makes strong players meet in round 1 of single elimination, which is unfair and less fun. In Swiss it causes lopsided early rounds.
- Random seeding is fair on average but often produces exactly those early mismatches.

### 2.2 Is AI the right tool?
| Option | Verdict |
|---|---|
| Manual seeding | Stays the default and is always available |
| Random seeding | Stays available, and suits casual nights |
| Simple rule (win percentage) | Ignores who you beat, and is noisy with few games. This is the baseline the AI must beat. |
| **Statistical rating model trained on local results** (Elo-style or Glicko-2) | **Proposed.** It learns strength from match outcomes, weights wins by opponent strength, and reports its own uncertainty. |
| Large language model | **Rejected.** It would send minors' data to a cloud service, needs a network connection, and adds nothing a rating model can't do here. |

### 2.3 When the feature should not be used
- The first event on a machine, or any event where most entrants have no history: the suggestion would be mostly guesswork.
- Events where the rules require random seeding.
- Events where the organizer's knowledge is better than the data, for example a strong new transfer student. The organizer overrides the suggestion.
- When the organizer hasn't turned the feature on (AI-FR-05).

## 3. Data (PAIR: *Data Collection + Evaluation*)

| Aspect | Requirement |
|---|---|
| **Source** | Only real match results already stored in the local Bracketeer database: both entrants, the score, the date and the format. No external data. |
| **Excluded** | Byes and matches without a score. Forfeits, if they're added later. |
| **Identity** | An entrant in a new event is linked to a past entrant **only when the organizer confirms it**. Matching on name or tag alone is not allowed, because tags such as JAV can collide. |
| **Minimum data** | A rating is shown only after ≥ 3 rated matches. Players with fewer are labelled *Unrated*. |
| **Location and retention** | Ratings are computed on the device and never uploaded. The organizer can view and delete any player's history (AI-FR-08). |
| **Minors** | The feature is off by default. The README states that turning it on creates a performance profile of players. |

## 4. Candidate model (not decided)

Elo or Glicko-2, computed locally from the match history. Glicko-2 is preferred because it gives a *rating deviation*, which is a measure of confidence that drives the explanations and the Unrated label. The choice will be recorded in an ADR if the feature is built.

## 5. Success metrics

| Metric | Target | How measured |
|---|---|---|
| **Seeding quality** | Spearman rank correlation between suggested seed and final placement is ≥ 0.2 higher than random seeding, and no worse than the win-percentage rule | Back-test on past events in the database. Ratings are computed **only from events before** the one being predicted, so there is no data leakage. |
| **Acceptance** | ≥ 70 % of suggested positions kept unchanged by organizers | Local count of accepted and moved positions only; no names logged |
| **Time saved** | Seeding a 16-player event takes < 1 minute with suggestions | Timed during a manual trial run |
| **Guardrail: fairness to new players** | Unrated players' average seed is no worse than under the organizer's chosen placement rule | Back-test (see F7) |

## 6. Failure modes and mitigations (PAIR: *Errors + Graceful Failure*)

| # | Failure mode | Effect | Mitigation |
|---|---|---|---|
| F1 | **Cold start**: no history | Meaningless suggestions | Show *Unrated*. Don't guess (HAX G10). |
| F2 | **Wrong identity link**: two different "JAV"s merged | One player inherits another's record | Links only on organizer confirmation, and links can be undone |
| F3 | **Stale rating**: a player improved over the summer | Under-seeded strong player | Confidence decays with time since the last game; the organizer can override |
| F4 | **Over-confidence from a small sample** | A lucky 3–0 newcomer seeded first | Rating deviation shown; minimum match count |
| F5 | **Feedback loop**: top seeds get byes, so they win more, so their rating goes up | Rich get richer | Byes are excluded from ratings; back-test checks for drift |
| F6 | **Sandbagging**: losing on purpose to get a low seed | Unfair draws | Out of scope for game nights, but documented. The organizer can always override. |
| F7 | **Bias against new or infrequent players** | Newcomers always seeded last | The placement rule for unrated players is the organizer's choice (open question Q1), never automatically last |
| F8 | **Automation bias**: the organizer accepts without looking | Errors pass unnoticed | Explanations shown by default; changes must be applied explicitly; consequences shown before applying (who gets byes) |
| F9 | **Corrupt or missing history** | Wrong ratings | Ratings are recomputed from match records, never stored as the only copy |

## 7. Functional requirements for human control and explanation

| ID | Requirement | HAX |
|---|---|---|
| AI-FR-01 | Suggestions appear only when the organizer presses **Suggest seeds**, and are applied only when they press **Apply**. | G7, G8 |
| AI-FR-02 | Each suggested position shows the rating, the number of rated matches and a confidence label (High / Medium / Low / Unrated). | G2, G11 |
| AI-FR-03 | After applying, the organizer can move any player. A manual change is never overwritten by a later suggestion. | G9 |
| AI-FR-04 | **Revert** restores the seed order from before the suggestion was applied, in one action. | G9 |
| AI-FR-05 | A global setting turns the feature on or off. It is **off** by default. | G17 |
| AI-FR-06 | Unrated players are placed by an organizer-chosen rule, and the rule is shown next to them. | G6 |
| AI-FR-07 | Explanation text for each player uses plain words, for example: *"Seed 2: rating 1610 from 14 matches in 3 events (medium confidence)."* | G11 |
| AI-FR-08 | The organizer can view and delete any player's rating history. | G17 |
| AI-FR-09 | Before applying, Bracketeer shows the consequences: which players would get byes and which round-1 pairings change. | G16 |
| AI-FR-10 | The first time the feature is used, it explains what it does and its limits: *"Based only on matches recorded in Bracketeer on this computer."* | G1 |
| AI-FR-11 | Ratings change only when a tournament is finished, never mid-event. | G14 |
| AI-FR-12 | If the rating method changes in a new version, the release notes and the first use after the update say so. | G18 |

## 8. Explanation and mental model (PAIR: *Mental Models*, *Explainability + Trust*)

- The mental model to build: *"Bracketeer remembers who beat whom here and suggests an order. I'm still in charge."*
- Explanations describe the evidence (matches, events, confidence), not the formula.
- Confidence is shown in words, which most users read more accurately than numbers.

## 9. Mapping to the guidance

### HAX (Microsoft, 18 guidelines)
| Guideline | Where |
|---|---|
| G1 Make clear what the system can do | AI-FR-10 |
| G2 Make clear how well the system can do what it can do | AI-FR-02 |
| G6 Mitigate social biases | AI-FR-06, F7 |
| G7 Support efficient invocation | AI-FR-01 |
| G8 Support efficient dismissal | AI-FR-01 (ignore the suggestion) |
| G9 Support efficient correction | AI-FR-03, AI-FR-04 |
| G10 Scope services when in doubt | F1 (*Unrated* instead of a guess) |
| G11 Make clear why the system did what it did | AI-FR-02, AI-FR-07 |
| G14 Update and adapt cautiously | AI-FR-11 |
| G16 Convey the consequences of user actions | AI-FR-09 |
| G17 Provide global controls | AI-FR-05, AI-FR-08 |
| G18 Notify users about changes | AI-FR-12 |

### PAIR (Google People + AI Guidebook chapters)
| Chapter | Section |
|---|---|
| User Needs + Defining Success | 2, 5 |
| Data Collection + Evaluation | 3, 5 |
| Mental Models | 8 |
| Explainability + Trust | 7, 8 |
| Feedback + Control | 7 |
| Errors + Graceful Failure | 6 |

## 10. Open questions (to settle in the final edit)
- **Q1** What is the default placement rule for unrated players: random among the middle seeds, after all rated players, or the organizer's manual order? (My current preference: after all rated players.)
- **Q2** Should ratings be separate per game title? Yes is more accurate, but leaves less data per rating.
- **Q3** Is a confirmation step for identity links enough, or does linking need its own screen?
- **Q4** Does turning the feature on for a school club need a note in the consent wording from US-12?

## Sources
- Microsoft HAX Toolkit, Guidelines for Human-AI Interaction: https://www.microsoft.com/en-us/haxtoolkit/
- Google People + AI Guidebook: https://pair.withgoogle.com/guidebook
- Glickman, M. E., *Example of the Glicko-2 system*: http://www.glicko.net/glicko/glicko2.pdf
