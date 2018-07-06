from collections import namedtuple
from game.scrabble_players import AIPlayer
from unittest import TestCase

import os

# Move up to the parent directory so that we can access the correct ground files.
os.chdir("../")

player = AIPlayer(id=1, init_tiles=['A', 'P', 'P', 'L', 'E', 'S', 'Z'])


class TestAIPlayer(TestCase):
    def test_find_words(self):
        # Test basic anagram of tiles
        found_words = set(player.find_words())
        self.assertTrue('APPLES' in found_words and 'APE' in found_words and 'PLEA' in found_words)

        # Test using mandated tiles on the board
        found_words = set(player.find_words(req_tiles=[('M',0)]))
        self.assertTrue('MAPLE' in found_words and 'MAZE' in found_words and 'APPLE' not in found_words)

        # Assert empty sets are returned when confronted with impossible demands
        found_words = set(player.find_words(req_tiles=[('M', 0), ('Z', 1)]))
        self.assertTrue(found_words == set([]))

    def test_ancillary_words(self):
        blank_board = [''.join([' ' for _ in range(15)]) for _ in range(15)]
        Move = namedtuple('move', 'coords dir word')
        test_board = blank_board.copy()
        test_board[1] = '    DOG        '

        # Test vertical word placement.
        test_move = Move((1, 7), 'D', 'SLAP')
        self.assertTrue(player.ancillary_valid(test_move, test_board))

        # Test Horizontal word placement
        test_move = Move((2, 6), 'R', 'ORANGE')
        self.assertTrue(player.ancillary_valid(test_move, test_board))

        # Test complex multiple word placement
        test_move = Move((2, 1), 'R', 'CHROMO')
        self.assertTrue(player.ancillary_valid(test_move, test_board))


