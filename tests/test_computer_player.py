"""ComputerPlayer tests."""

from __future__ import annotations

import string
from typing import ClassVar
from unittest import TestCase

from game.players.computer import ComputerPlayer
from game.rulebook import Rulebook


class TestComputerPlayer(TestCase):
    rb: ClassVar[Rulebook]

    @classmethod
    def setUpClass(cls) -> None:
        cls.rb = Rulebook()

    def test_find_words(self) -> None:
        player = ComputerPlayer(
            player_id=1,
            rulebook=self.rb,
            init_tiles=["A", "P", "P", "L", "E", "?", "Z"],
            name="test1",
        )

        found_words = set(player.find_words())
        self.assertTrue("APPLE" in found_words and "APE" in found_words and "PLEA" in found_words)

        found_words = set(player.find_words())
        self.assertTrue("APPLEs" in found_words)

        found_words = set(player.find_words(fixed_tiles=(("M", 0),)))
        self.assertTrue("MAPLE" in found_words and "MAZE" in found_words and "APPLE" not in found_words)

        found_words = set(player.find_words(fixed_tiles=(("M", 0), ("Z", 1))))
        self.assertEqual(found_words, set())

        found_words = set(
            player.find_words(min_length=4, max_length=9, fixed_tiles=(("D", 4), ("S", 5)))
        )
        self.assertTrue("PLEADS" in found_words)
        self.assertTrue("SPA" not in found_words)

        self.assertTrue(
            all(
                (len(word) == 5 and word[4] == "D")
                or (len(word) == 6 and word[4] == "D" and word[5] == "S")
                for word in found_words
            )
        )

        found_words = set(player.find_words(min_length=1, max_length=8, fixed_tiles=(("S", 0),)))
        self.assertTrue("SAP" in found_words)
        self.assertTrue("SPAcE" in found_words)
        self.assertTrue(all(word[0] == "S" for word in found_words))

        found_words = set(player.find_words(min_length=1, max_length=8, fixed_tiles=(("S", 4),)))
        self.assertTrue("PLEA" not in found_words and "PLEAS" in found_words)

    def test_get_move_params(self) -> None:
        player = ComputerPlayer(
            player_id=1,
            rulebook=self.rb,
            init_tiles=["A", "P", "P", "L", "E", "?", "Z"],
            name="test1",
        )
        board_state = [" " * 15 for _ in range(15)]

        board_state[7] = " " * 7 + "S" + " " * 7

        move_param = player.get_move_params((7, 5), "R", board_state)
        self.assertEqual(move_param, (2, [("S", 2)]))

        move_param = player.get_move_params((7, 7), "R", board_state)
        self.assertEqual(move_param, (1, [("S", 0)]))

        move_param = player.get_move_params((7, 0), "R", board_state)
        self.assertEqual(move_param, (7, [("S", 7)]))

        board_state[7] = " " + "".join([string.ascii_uppercase[i] for i in range(14)])
        self.assertEqual(len(board_state[7]), 15)
        presumed_fixed = [(letter, index + 1) for index, letter in enumerate(string.ascii_uppercase[:14])]
        move_param = player.get_move_params((7, 0), "R", board_state)
        self.assertEqual(move_param, (1, presumed_fixed))

        board_state[7] = " " + "".join([string.ascii_uppercase[i] if i % 2 == 0 else " " for i in range(14)])
        presumed_fixed = [
            (letter, index + 1)
            for index, letter in enumerate(string.ascii_uppercase[:14])
            if index % 2 == 0
        ]
        move_param = player.get_move_params((7, 0), "R", board_state)
        self.assertEqual(move_param, (1, presumed_fixed))

        board_state[7] = " " * 7 + "S" + " " * 7
        move_param = player.get_move_params((6, 7), "R", board_state)
        self.assertEqual(move_param, (1, []))

        board_state[7] = " " * 7 + "S" + " " * 7
        board_state[6] = " " * 13 + "NG"
        move_param = player.get_move_params((6, 7), "R", board_state)
        self.assertEqual(move_param, (1, [("N", 6), ("G", 7)]))
