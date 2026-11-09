# Domain Rules

These are the tournament rules Bracketeer enforces. They hold the precise detail behind the [user stories](user-stories.md). Each rule has an ID (for example, `R-RS-2`), so stories and tests can refer to it without restating it. Every rule is stated once, here, so a change to a rule happens in one place.

## Glossary

| Term                  | Meaning                                                                 |
| --------------------- | ----------------------------------------------------------------------- |
| **Organizer**         | The person running the tournament and using Bracketeer                  |
| **Player**            | A registered participant (a person or a team)                           |
| **Seed**              | A player's starting rank, from 1 (strongest) to _n_                     |
| **Round**             | A set of matches played at the same stage of the tournament             |
| **Match**             | One pairing of two players within a round                               |
| **Game score**        | The number of games (or points) each player won in a match, such as 2–1 |
| **Bye**               | A round in which a player has no opponent                               |
| **Forfeit**           | A match one player loses without playing, recorded by the organizer     |
| **Match points**      | Points earned from match results; standings are ranked by these first   |
| **Game differential** | Games won minus games lost                                              |
| **Standings**         | The ranked list of all players                                          |

## Players (R-PL)

- **R-PL-1.** A tournament has between 2 and 64 players.
- **R-PL-2.** Every player has a name of 1–40 characters, after leading and trailing spaces are trimmed. Names are unique within a tournament, ignoring upper and lower case ("Ana" and "ana" count as the same name).
- **R-PL-3.** A player may have an optional rating: a whole number of 0 or more.
- **R-PL-4.** Players can be added, edited, or removed only before the tournament starts. After it starts, a player's name can still be corrected, but players can't be added or removed. A player who leaves mid-tournament stays registered; the organizer records a forfeit for each of their remaining matches (R-RS-5).

## Seeding (R-SD)

- **R-SD-1.** Before the tournament starts, every player has a unique seed from 1 to _n_.
- **R-SD-2.** The organizer can seed players in three ways:
  - **Manually:** the organizer sets the order.
  - **Randomly:** every order is equally likely.
  - **By rating:** highest rating first. Players with equal ratings keep their registration order. Unrated players come after all rated players, in registration order.
- **R-SD-3.** Seeds are fixed when the tournament starts. The original seed is used as the final tiebreaker (R-TB-3).

## Rounds (R-RD)

- **R-RD-1.** In single elimination, the next round is generated only after every result in the current round has been entered.
- **R-RD-2.** No player appears more than once in the same round.
- **R-RD-3.** In round robin, a round contains at most one bye. In single elimination, only round 1 can have byes, as R-SE-1 sets out.
- **R-RD-4.** A tournament is complete when the last round's results are all entered.

## Results and scoring (R-RS)

- **R-RS-1.** A result is two game scores, each a whole number of 0 or more. The higher score wins. Equal scores are a draw.
- **R-RS-2.** Draws are allowed in round robin. In single elimination, a result with equal scores is rejected, because someone must advance.
- **R-RS-3.** Match points: a win is worth 3, a draw 1, and a loss 0.
- **R-RS-4.** A bye is neither a win nor a loss. It gives no match points and no game score. In round robin with an odd _n_, every player gets exactly one bye (R-RR-2), so byes don't change the final order. In single elimination, a bye only means the player advances (R-SE-1).
- **R-RS-5.** Instead of game scores, the organizer can record a forfeit when a player doesn't play a match (for example, they didn't show up or left the event). The forfeit names the player who forfeited, who must be one of the match's two players. It counts as a win for the opponent (3 match points) and a loss for the forfeiting player (0). No game score is recorded for it. A forfeit is never a draw, so it's allowed in every format; in single elimination, the opponent advances.
- **R-RS-6.** Game differential counts only matches with game scores. Byes and forfeits don't affect it.
- **R-RS-7.** In single elimination, a result can't be changed or cleared once the next round has been generated, because that round's pairings depend on it. In round robin, results can be changed at any time, because the schedule doesn't depend on results.

## Single elimination (R-SE)

- **R-SE-1.** The bracket size is the smallest power of 2 that is at least _n_. The number of byes is the bracket size minus _n_. Byes go to the top seeds in round 1.
- **R-SE-2.** Players are placed in the standard bracket order, so that seeds 1 and 2 can meet only in the final. For example, with 8 players, round 1 is 1 v 8, 4 v 5, 2 v 7, and 3 v 6.
- **R-SE-3.** The winner of each match advances and the loser is eliminated. A tournament with _n_ players has exactly _n_ − 1 matches. Byes aren't matches.
- **R-SE-4.** Final placement depends on the round in which a player was eliminated. The champion is 1st and the finalist is 2nd. The two losing semifinalists share 3rd, the four losing quarterfinalists share 5th, and so on. There is no 3rd-place match.

## Round robin (R-RR)

- **R-RR-1.** Every pair of players meets exactly once, so there are _n_(_n_ − 1)/2 matches. The schedule is made with the circle method.
- **R-RR-2.** With an even _n_, there are _n_ − 1 rounds. With an odd _n_, there are _n_ rounds, each round has one bye, and every player gets exactly one bye.
- **R-RR-3.** The whole schedule is generated when the tournament starts.

Because every player gets exactly one bye when _n_ is odd, byes don't change the final order (R-RS-4). Partway through, a player who has had their bye has played one match fewer than some others, so the standings show matches played (US-09 #6).

## Standings and tiebreakers (R-TB)

- **R-TB-1.** Standings list every registered player exactly once.
- **R-TB-2.** In round robin, players are ranked by these criteria, in order: match points, then game differential, then original seed.
- **R-TB-3.** The original seed is the final tiebreaker: the lower seed number ranks higher. This guarantees that the standings always have one complete, repeatable order.
- **R-TB-4.** In single elimination, standings follow the placements in R-SE-4. Players who share a placement are listed by seed.

## Sources

- Round-robin tournaments (circle method): https://en.wikipedia.org/wiki/Round-robin_tournament
- Single-elimination tournaments (byes, seeding): https://en.wikipedia.org/wiki/Single-elimination_tournament
