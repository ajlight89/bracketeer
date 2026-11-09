# AI Feature Proposal: Smart Seeding

- **Status:** Proposed (not planned for v1.0; MoSCoW: Won't have this release)

This document applies AI requirements practices to a possible future feature. Nothing here is built in v1.0. The requirements are organized around the NIST AI Risk Management Framework (AI RMF 1.0): its four functions (Govern, Map, Measure, Manage) and its seven characteristics of trustworthy AI.

## 1. The idea

v1.0 can seed players by a rating the organizer types in (R-SD-2 in [domain-rules.md](domain-rules.md)). That is a plain sort, not AI. Ratings are often missing, out of date, or taken from different sources that don't agree.

**Smart Seeding** would _estimate_ each player's skill from their match results in earlier Bracketeer tournaments, and suggest a seeding order based on those estimates. The organizer always reviews the suggestion and decides.

**Why this counts as AI:** NIST describes an AI system as an engineered system that, for a given set of objectives, generates outputs such as predictions or recommendations. A skill model trained on past results predicts match outcomes and recommends seeds, so it falls under that description. That's true even though the method is classical statistics rather than a neural network.

**Candidate methods:** a paired-comparison model fitted to past results (Bradley–Terry), or a rating system that also tracks its own uncertainty (Glicko-2). Both are well documented and explainable. The method would be chosen by the evaluation in section 4, not in advance.

### Proposed user story

As an organizer, I want Bracketeer to suggest seeds based on players' past results so that I can seed fairly even when ratings are missing or out of date.

1. **Given** players with enough match history (AI-DA-1), **when** I ask for suggested seeds, **then** I see a suggested order, and each player shows a short reason.
2. **Given** I'm shown suggested seeds, **when** I don't confirm them, **then** the seeds stay exactly as they were.
3. **Given** some players have too little history, **then** those players are placed by the baseline method and labeled "not enough history".
4. **Given** I'm shown suggested seeds, **when** I edit the order and confirm, **then** my edited order is used.

## 2. Map: context and intended use

| Item            | Description                                                                                                                                                                                      |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Intended use    | Suggesting a starting seed order for one tournament                                                                                                                                              |
| Users           | The tournament organizer                                                                                                                                                                         |
| People affected | The players, whose seeds affect their opponents and byes                                                                                                                                         |
| Stakes          | Low to moderate: unfair seeding can change results, prizes, and how fair players feel the event is. No safety, financial, or legal decisions depend on it.                                       |
| Out of scope    | Ranking players outside a tournament, deciding who is eligible to enter, or splitting prizes. The suggestion must not be presented as a measure of a person's worth or ability outside the game. |

**Data prerequisite:** in v1.0, a player exists only inside one tournament, and names only need to be unique within that tournament (R-PL-2). Smart Seeding would need **a player identity that persists across tournaments**, so that two different players who are both called "Alex" don't get merged. This is a new data requirement. The v1.0 save format should not rule it out: every player already has an ID within a tournament, and a later version could link those IDs to a lasting player record.

## 3. Requirements by trustworthiness characteristic

### Valid and reliable (VR)

| ID      | Requirement                                                                                                                                                                                                                                                     |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AI-VR-1 | Smart Seeding must beat the **baseline** on the evaluation in section 4. The baseline is the v1.0 seeding: sort by rating, with unrated players after rated players in registration order (R-SD-2). If it doesn't beat the baseline, the feature isn't shipped. |
| AI-VR-2 | The same data always produces the same suggestion (no randomness in the output).                                                                                                                                                                                |
| AI-VR-3 | Only real games count as evidence of skill. **Byes and forfeits are excluded** from the training data, because they say nothing about how well a player plays.                                                                                                  |

### Safe (SA)

| ID      | Requirement                                                                                                           |
| ------- | --------------------------------------------------------------------------------------------------------------------- |
| AI-SA-1 | Suggestions never change a tournament that has already started. Seeds stay fixed once the tournament starts (R-SD-3). |

### Secure and resilient (SR)

| ID      | Requirement                                                                                                                                                                                                               |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AI-SR-1 | If the history is missing, damaged, or too thin, or if the estimate fails, Bracketeer falls back to the baseline and says so. It never shows an error in place of seeds.                                                  |
| AI-SR-2 | **Sandbagging** (losing on purpose in earlier events to get an easier seed) is a known way to game the system. The organizer can see each player's history behind a suggestion, so suspicious drops in skill are visible. |

### Accountable and transparent (AT)

| ID      | Requirement                                                                                                                                                                  |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AI-AT-1 | **Human oversight:** suggestions are never applied automatically. The organizer reviews, edits, and confirms them. The organizer is accountable for the seeds that are used. |
| AI-AT-2 | The tournament records whether its seeds came from a suggestion, and which model version produced it.                                                                        |
| AI-AT-3 | The model, its data, and its evaluation results are documented in the repository.                                                                                            |

### Explainable and interpretable (EI)

| ID      | Requirement                                                                                                                       |
| ------- | --------------------------------------------------------------------------------------------------------------------------------- |
| AI-EI-1 | Each suggested seed shows a short reason in plain language, for example: "Won 9 of 14 matches in 3 earlier tournaments."          |
| AI-EI-2 | Each suggestion shows how confident it is (for example, high, medium, or low, based on how much history the player has).          |
| AI-EI-3 | The organizer can see the suggestion side by side with the baseline order, with players who move far between the two highlighted. |

### Privacy-enhanced (PR)

| ID      | Requirement                                                                                                                                                                   |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AI-PR-1 | All data and all calculation stay on the organizer's computer. Nothing is sent to a third-party service (consistent with NFR-SE-5 in [non-functional.md](non-functional.md)). |
| AI-PR-2 | The organizer can delete a player's match history, and the deleted history isn't used in later suggestions.                                                                   |

### Fair, with harmful bias managed (FB)

| ID      | Requirement                                                                                                                                                                                                                               |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AI-FB-1 | **New players** (the "cold start" problem) are not automatically seeded last. They are placed by the baseline (their rating if they have one, otherwise registration order) and labeled "not enough history".                             |
| AI-FB-2 | **Feedback loop:** top seeds get easier paths, which can inflate their results and keep them at the top. The model must account for opponent strength (as Bradley–Terry and Glicko-2 do), not just count wins. Section 4 checks for this. |
| AI-FB-3 | Players who play often get more confident estimates than players who play rarely. That difference is shown to the organizer (AI-EI-2), not hidden.                                                                                        |

## 4. Measure: data and evaluation plan

### Data requirements (DA)

| ID      | Requirement                                                                                                                                                                                                |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AI-DA-1 | A player's estimate is trusted only after **at least 10 counted matches across at least 3 tournaments**. Below that, AI-FB-1 applies. These thresholds are starting points, to be tuned by the evaluation. |
| AI-DA-2 | Only completed matches with game scores are used (AI-VR-3).                                                                                                                                                |
| AI-DA-3 | The evaluation needs at least 20 completed tournaments that weren't used for training.                                                                                                                     |

### Evaluation

- **Metric:** **Spearman's rank correlation (ρ)** between each player's seed and their final placement. A ρ of 1 means the seeds predicted the final order perfectly; a ρ of 0 means they predicted nothing. Players who share a placement (such as shared 3rd) get the average of the ranks they share.
- **Method:** a **time-based split**. The model is trained only on tournaments that happened before each test tournament, so it never "sees the future". Both the baseline and Smart Seeding are scored on the same test tournaments.
- **Pass condition:** across the test tournaments, the average ρ for Smart Seeding must be **at least 0.05 higher** than the baseline's. A bootstrap 95% confidence interval for that difference must not include zero. If the evaluation can't show this, the feature isn't shipped (AI-VR-1).
- **Fairness check:** the comparison is repeated separately for players with little history and players with a lot of history. Smart Seeding must not do worse than the baseline for the low-history group.
- **Feedback-loop check:** results are compared separately for top-half and bottom-half seeds. The model shouldn't do better mainly at "confirming" the players it already seeded high.

## 5. Manage: failure modes and responses

| Failure                                     | Effect                                     | Response                                                                                                                                                                      |
| ------------------------------------------- | ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Too little history                          | Unreliable estimate                        | Baseline placement plus a label (AI-FB-1)                                                                                                                                     |
| Two players merged under one identity       | Wrong history, wrong seed                  | Persistent player IDs (section 2); the organizer can see the history behind each suggestion (AI-SR-2)                                                                         |
| A skilled player seeded too low             | Strong players meet early                  | The organizer reviews and edits before confirming (AI-AT-1); large moves are highlighted (AI-EI-3)                                                                            |
| Sandbagging                                 | One player gains an easier path            | The history is visible (AI-SR-2); the organizer decides                                                                                                                       |
| The model gets worse over time              | Seeds become less useful than the baseline | After each tournament, record ρ for both methods. If Smart Seeding has lost to the baseline over the last 10 tournaments, it switches off by default and tells the organizer. |
| The estimate fails or the data is corrupted | No suggestion                              | Fall back to the baseline with a message (AI-SR-1)                                                                                                                            |

## 6. Govern: responsibilities

- **The organizer** is accountable for the seeds a tournament uses, whether they were suggested or not (AI-AT-1).
- **The developer** is accountable for the model's documentation, its evaluation results (AI-AT-3), and for not shipping it unless it beats the baseline (AI-VR-1).
- Any decision to build this feature would be recorded in [key-decisions.md](../key-decisions.md).

## Sources

- NIST AI Risk Management Framework 1.0 (NIST AI 100-1): https://doi.org/10.6028/NIST.AI.100-1
- Bradley–Terry model: https://en.wikipedia.org/wiki/Bradley%E2%80%93Terry_model
- Glicko-2 rating system (Mark Glickman): http://www.glicko.net/glicko/glicko2.pdf
- Elo rating system (background on rating-based skill estimates): https://en.wikipedia.org/wiki/Elo_rating_system
- Spearman's rank correlation coefficient: https://en.wikipedia.org/wiki/Spearman%27s_rank_correlation_coefficient
- Bootstrapping (statistics): https://en.wikipedia.org/wiki/Bootstrapping_(statistics)
