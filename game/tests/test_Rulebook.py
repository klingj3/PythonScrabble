from collections import namedtuple
from game.scrabble_box import Rulebook
from unittest import TestCase

import os

# Move up to the parent directory so that we can access the correct ground files.
os.chdir("../")

rulebook = Rulebook()

class TestRulebook(TestCase):
    def test_score_moves(self):
        # Test that moves are recognized as being valid.

        blank_board = [''.join([' ' for _ in range(15)]) for _ in range(15)]
        Move = namedtuple('move', 'coords dir word')
        test_board = blank_board.copy()
        test_board[1] = '    DOG        '

        # Test vertical word placement.
        test_move = Move((1, 7), 'D', 'SLAP')
        self.assertTrue(rulebook.score_move(test_move, test_board) > 0)

        # Test Horizontal word placement
        test_move = Move((2, 6), 'R', 'ORANGE')
        self.assertTrue(rulebook.score_move(test_move, test_board) > 0)

        # Test complex multiple word placement
        test_move = Move((2, 1), 'R', 'CHROMO')
        self.assertTrue(rulebook.score_move(test_move, test_board) > 0)

        #  Check invalid placement
        test_move = Move((2, 1), 'R', 'CRUNCH')
        self.assertFalse(rulebook.score_move(test_move, test_board) < 0)


