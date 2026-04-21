"""HumanPlayer rack checks and exchange parsing."""

from __future__ import annotations

from typing import ClassVar
from unittest import TestCase

from game.players.human import HumanPlayer
from game.rulebook import Rulebook
from game.types import Move


def _empty_board() -> list[str]:
    return ["".join(" " for _ in range(15)) for _ in range(15)]


class TestHumanPlayerTilesPresent(TestCase):
    rb: ClassVar[Rulebook]

    @classmethod
    def setUpClass(cls) -> None:
        cls.rb = Rulebook()

    def test_word_may_end_on_right_edge(self) -> None:
        """A word may end on file/rank 14 (bounds use last index, not word length)."""
        board = _empty_board()
        p = HumanPlayer(1, ["S", "P", "I", "N", "A", "O", "T"], self.rb, name="t")
        move = Move((8, 11), "R", "SPIN")
        self.assertTrue(p._tiles_present(move, board))

    def test_word_may_end_on_bottom_edge(self) -> None:
        board = _empty_board()
        p = HumanPlayer(1, ["S", "P", "I", "N", "A", "O", "T"], self.rb, name="t")
        move = Move((11, 8), "D", "SPIN")
        self.assertTrue(p._tiles_present(move, board))

    def test_word_extending_past_edge_rejected(self) -> None:
        board = _empty_board()
        p = HumanPlayer(1, ["S", "P", "I", "N", "A", "O", "T"], self.rb, name="t")
        move = Move((8, 12), "R", "SPIN")
        self.assertFalse(p._tiles_present(move, board))

    def test_blank_covers_second_duplicate_letter(self) -> None:
        """A second matching letter can come from a blank after the first is used."""
        board = _empty_board()
        p = HumanPlayer(1, ["S", "?", "A", "B", "C", "D", "E"], self.rb, name="t")
        move = Move((7, 7), "R", "SS")
        self.assertTrue(p._tiles_present(move, board))


class TestHumanPlayerExchange(TestCase):
    rb: ClassVar[Rulebook]

    @classmethod
    def setUpClass(cls) -> None:
        cls.rb = Rulebook()

    def test_exchange_lowercase_input_matches_uppercase_rack(self) -> None:
        """Exchange input is normalised to uppercase so rack removal matches tiles."""
        board = _empty_board()
        p = HumanPlayer(1, ["Z", "L", "E", "I", "I", "I", "O"], self.rb, name="t")
        move = p._interpret(["exchange", "iii"], board)
        self.assertEqual(move, Move((-2, -2), "", "III"))
        for ch in move.word:
            p.tiles.remove(ch)
        self.assertEqual(sorted(p.tiles), ["E", "L", "O", "Z"])
