"""GameMaster tests."""

from __future__ import annotations

from unittest import TestCase

from game.game_master import GameMaster


class TestGameMaster(TestCase):
    def test_reset_creates_players_and_scores(self) -> None:
        gm = GameMaster(human_count=0, computer_count=2)
        gm.reset_game()
        self.assertEqual(len(gm.players), 2)
        self.assertEqual(len(gm.player_scores), 2)
        self.assertTrue(all(s == 0 for s in gm.player_scores))
        self.assertIsNotNone(gm.board)
        self.assertIsNotNone(gm.bag)
