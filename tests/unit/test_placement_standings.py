"""Unit tests for single elimination placement standings (US-09 #5, R-TB-4)."""

from bracketeer.domain.player import Player
from bracketeer.domain.rounds import Match, Round
from bracketeer.domain.standings import placement_standings
from bracketeer.domain.values import PlayerName, Result


def seeded_players(count):
    """Players 1 to count, where player n is seed n."""
    return [Player(n, PlayerName(f"Player {n}"), None, n) for n in range(1, count + 1)]


def won(match_id, winner, loser):
    """A match the first player won 2-0."""
    return Match(match_id, winner, loser, Result.played(2, 0))


def eight_player_bracket():
    """A finished 8-player bracket with upsets.

    Seeds 5 and 6 reach the semifinals, and seed 2 beats seed 1 in the final.
    """
    quarterfinals = Round(1, [won(1, 1, 8), won(2, 5, 4), won(3, 2, 7), won(4, 6, 3)])
    semifinals = Round(2, [won(5, 1, 5), won(6, 2, 6)])
    final = Round(3, [won(7, 2, 1)])
    return [quarterfinals, semifinals, final]


def ranks_by_player(players, rounds):
    return {s.player_id: s.rank for s in placement_standings(players, rounds)}


def test_the_champion_is_first_and_the_finalist_second():
    # US-09 #5, R-SE-4
    ranks = ranks_by_player(seeded_players(8), eight_player_bracket())
    assert ranks[2] == 1
    assert ranks[1] == 2


def test_the_losing_semifinalists_share_third():
    # US-09 #5, R-SE-4
    ranks = ranks_by_player(seeded_players(8), eight_player_bracket())
    assert ranks[5] == ranks[6] == 3


def test_the_losing_quarterfinalists_share_fifth():
    # US-09 #5, R-SE-4
    ranks = ranks_by_player(seeded_players(8), eight_player_bracket())
    assert [ranks[p] for p in (3, 4, 7, 8)] == [5, 5, 5, 5]


def test_players_who_share_a_placement_are_listed_by_seed():
    # R-TB-4
    standings = placement_standings(seeded_players(8), eight_player_bracket())
    assert [s.player_id for s in standings] == [2, 1, 5, 6, 3, 4, 7, 8]


def test_players_still_in_share_first_place():
    # US-09 #1: the standings are up to date after every round
    quarterfinals_only = eight_player_bracket()[:1]
    ranks = ranks_by_player(seeded_players(8), quarterfinals_only)
    assert [ranks[p] for p in (1, 2, 5, 6)] == [1, 1, 1, 1]
    assert [ranks[p] for p in (3, 4, 7, 8)] == [5, 5, 5, 5]


def test_a_bye_is_not_a_loss():
    # R-RS-4: seed 1 has a bye and is still in
    first_round = Round(1, [won(1, 2, 3)], byes=[1])
    ranks = ranks_by_player(seeded_players(3), [first_round])
    assert ranks == {1: 1, 2: 1, 3: 3}


def test_a_forfeit_knocks_the_forfeiting_player_out():
    # R-RS-5
    final = Round(1, [Match(1, 1, 2, Result.forfeit(1))])
    ranks = ranks_by_player(seeded_players(2), [final])
    assert ranks == {1: 2, 2: 1}


def test_every_player_is_listed_before_any_results():
    # US-09 #2
    standings = placement_standings(seeded_players(4), [])
    assert [s.player_id for s in standings] == [1, 2, 3, 4]
    assert all(s.rank == 1 for s in standings)


def test_placement_rows_still_count_wins_losses_and_games():
    # US-09 #6
    standings = placement_standings(seeded_players(8), eight_player_bracket())
    champion, finalist = standings[0], standings[1]
    assert (champion.wins, champion.losses, champion.game_differential) == (3, 0, 6)
    assert (finalist.wins, finalist.losses, finalist.game_differential) == (2, 1, 2)
