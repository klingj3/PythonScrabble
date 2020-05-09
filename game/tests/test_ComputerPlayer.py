from game.scrabble_box import Rulebook
from game.scrabble_players import ComputerPlayer
from unittest import TestCase

import os
import string

# Move up to the parent directory so that we can access the correct ground files.
os.chdir("../..")
rb = Rulebook()


class TestComputerPlayer(TestCase):
    def test_find_words(self):
        player = ComputerPlayer(id=1, rulebook=rb, init_tiles=['A', 'P', 'P', 'L', 'E', '?', 'Z'], name='test1')

        """
        Tests using player's tiles
        """
        # Test basic anagram of tiles
        found_words = set(player.find_words())
        self.assertTrue('APPLE' in found_words and 'APE' in found_words and 'PLEA' in found_words)

        # Test that blank words are being created appropriately.
        found_words = set(player.find_words())
        self.assertTrue('APPLEs' in found_words)

        """
        Tests using tiles on board, and with meeting the restrictions of given move parameters. 
        """
        # Test using mandated tiles on the board
        found_words = set(player.find_words(fixed_tiles=[('M', 0)]))
        self.assertTrue('MAPLE' in found_words and 'MAZE' in found_words and 'APPLE' not in found_words)

        # Assert empty sets are returned when confronted with impossible demands
        found_words = set(player.find_words(fixed_tiles=[('M', 0), ('Z', 1)]))
        self.assertEqual(found_words, set([]))

        """
        Check that correct words are being generated with the tighter constraints of minimum and maximum word 
        lengths. 
        """
        found_words = set(player.find_words(min_length=4, max_length=9, fixed_tiles=[('D', 4), ('S', 5)]))
        self.assertTrue('PLEADS' in found_words)
        self.assertTrue('SPA' not in found_words)

        """
        Check that all words meet the minimum length for move legality, and that for the words which surpass that
        length have the required tiles in the correct positions.
        
        (Some of the words found here will be invalid, but that's checked at the next position)
        """
        self.assertTrue(all([
            (len(word) == 5 and word[4] == 'D') or
            (len(word) == 6 and word[4] == 'D' and word[5] == 'S')
            for word in found_words
        ]))

        """
        Similar check, but with the starting words.
        """

        found_words = set(player.find_words(min_length=1, max_length=8, fixed_tiles=[('S', 0)]))
        self.assertTrue('SAP' in found_words)
        self.assertTrue('SPAcE' in found_words)
        self.assertTrue(all([
            word[0] == 'S'
            for word in found_words
        ]))

        """
        Check that if a word terminates one tile behind a required tile, that word is not considered valid. 
        """
        found_words = set(player.find_words(min_length=1, max_length=8, fixed_tiles=[('S', 4)]))
        self.assertTrue('PLEA' not in found_words and 'PLEAS' in found_words)

    def test_get_move_params(self):
        player = ComputerPlayer(id=1, rulebook=rb, init_tiles=['A', 'P', 'P', 'L', 'E', '?', 'Z'], name='test1')
        board_state = [' '*15 for _ in range(15)]

        """
        We'll place an S tile in the center of the board. This is an illegal board position, but we'll overlook that 
        for testing as it makes for a valuable test case. 
        """
        board_state[7] = ' '*7 + 'S' + ' '*7

        """
        We check that it's discovered that at least two tiles must be played in order to meet legality, and that the
        third tile in the eventual word must be S if we start from the provided coordinates.
        """
        move_param = player.get_move_params((7, 5), 'R', board_state)
        self.assertEqual(move_param, (2, [('S', 2)]))

        """
        We now check that if we are starting our move from this center tile with an S on it, it is correctly labeled
        as the first letter of the board, this first tile asserts the game validity, and the maximum length of any 
        played word is 8 tiles. 
        """
        move_param = player.get_move_params((7, 7), 'R', board_state)
        self.assertEqual(move_param, (1, [('S', 0)]))

        """
        Check that if the board letters trail the seven played tiles, we correctly assert not only the validity of this
        move, but that the maximum length of a word resulting from this move is 8 tiles.
        """
        move_param = player.get_move_params((7, 0), 'R', board_state)
        self.assertEqual(move_param, (7, [('S', 7)]))

        """
        Having asserted that this works for single letters, we'll provide and additional check for longer strings.
        """
        board_state[7] = ' ' + ''.join([string.ascii_uppercase[i] for i in range(14)])
        assert(len(board_state[7]) == 15)
        presumed_fixed = [(letter, index+1) for index, letter in enumerate(string.ascii_uppercase[:14])]
        move_param = player.get_move_params((7, 0), 'R', board_state)
        self.assertEqual(move_param, (1, presumed_fixed))

        """
        We also check for interspaced tiles, such as a board with "  X  A B  ...".
        """
        board_state[7] = ' ' + ''.join([string.ascii_uppercase[i] if i%2 == 0 else ' ' for i in range(14)])
        presumed_fixed = [(letter, index+1) for index, letter in enumerate(string.ascii_uppercase[:14])
                          if index % 2 == 0]
        move_param = player.get_move_params((7, 0), 'R', board_state)
        self.assertEqual(move_param, (1, presumed_fixed))

        """
        Check that words neighboring, but not intersecting, existing words are treated as valid. 
        """
        board_state[7] = ' '*7 + 'S' + ' '*7
        move_param = player.get_move_params((6, 7), 'R', board_state)
        self.assertEqual(move_param, (1, []))

        """
        Lastly, check for both cases where early legality is determined by a move neighboring an existing tile,
        but also saves the correct information regarding maximum length and fixed tiles due to later intersectionality.
        """
        board_state[7] = ' '*7 + 'S' + ' '*7
        board_state[6] = ' '*13 + 'NG'
        move_param = player.get_move_params((6, 7), 'R', board_state)
        self.assertEqual(move_param, (1, [('N', 6), ('G', 7)]))
