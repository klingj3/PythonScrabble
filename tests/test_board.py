"""Board tests."""

from __future__ import annotations

from unittest import TestCase

from game.board import Board
from game.types import Move


class TestBoard(TestCase):
    def test_play_move_right(self) -> None:
        b = Board()
        m = Move((7, 7), "R", "HI")
        b.play_move(m)
        self.assertIn("H", b.state[7])
        self.assertIn("I", b.state[7])

    def test_play_move_down(self) -> None:
        b = Board()
        m = Move((5, 5), "D", "GO")
        b.play_move(m)
        self.assertEqual(b.state[5][5], "G")
        self.assertEqual(b.state[6][5], "O")
