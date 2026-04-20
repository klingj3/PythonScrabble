"""Tests for :class:`game.rulebook.Rulebook`."""

from __future__ import annotations

from typing import ClassVar
from unittest import TestCase

from game.rulebook import Rulebook
from game.types import Move


class TestRulebook(TestCase):
    rulebook: ClassVar[Rulebook]

    @classmethod
    def setUpClass(cls) -> None:
        cls.rulebook = Rulebook()

    def test_score_moves(self) -> None:
        blank_board = ["".join([" " for _ in range(15)]) for _ in range(15)]
        test_board = blank_board.copy()
        test_board[1] = "    DOG        "

        test_move = Move((1, 7), "D", "SLAP")
        self.assertTrue(self.rulebook.score_move(test_move, test_board) > 0)

        test_move = Move((2, 6), "R", "ORANGE")
        self.assertTrue(self.rulebook.score_move(test_move, test_board) > 0)

        test_move = Move((2, 1), "R", "CHROMO")
        self.assertTrue(self.rulebook.score_move(test_move, test_board) > 0)

        test_move = Move((2, 1), "R", "CRUNCH")
        self.assertEqual(self.rulebook.score_move(test_move, test_board), -1)

        test_move = Move((2, 1), "R", "ZXVY")
        self.assertEqual(self.rulebook.score_move(test_move, test_board), -1)

        test_move = Move((7, 7), "R", "QI")
        self.assertEqual(self.rulebook.score_move(test_move, blank_board), 22)
        test_board = blank_board.copy()
        test_board[8] = " " * 7 + "I" + " " * 7

        test_move = Move((7, 7), "R", "QI")
        self.assertEqual(self.rulebook.score_move(test_move, test_board), 44)

        test_board = blank_board.copy()
        test_board[14] = " " + "U" + " " * 13
        test_move = Move((14, 0), "R", "QUINTETS")
        self.assertEqual(self.rulebook.score_move(test_move, test_board, allow_illegal=True), 50 + 18 * 9)
