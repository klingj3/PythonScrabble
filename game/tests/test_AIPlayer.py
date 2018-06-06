from game.scrabble_players import AIPlayer
from unittest import TestCase

import os

# Move up to the parent directory so that we can access the correct ground files.
os.chdir("../")

class TestAIPlayer(TestCase):
    def test_find_words(self):
        player = AIPlayer(id=1, init_tiles=['A', 'P', 'P', 'L', 'E', 'Q', 'Z'])

        # Test basic anagram of tiles
        found_words = set(player.find_words())
        self.assertTrue('APPLE' in found_words and 'APE' in found_words and 'PLEA' in found_words)

        # Test using mandated tiles on the board
        found_words = set(player.find_words(req_tiles=[('M',0)]))
        self.assertTrue('MAPLE' in found_words and 'MAZE' in found_words and 'APPLE' not in found_words)

        # Assert empty sets are returned when confronted with impossible demands
        found_words = set(player.find_words(req_tiles=[('M',0), ('Z',1)]))
        self.assertTrue(found_words == set([]))

    def test_test_word(self):
        player = AIPlayer(id=1, init_tiles=['A', 'P', 'P', 'L', 'E', 'Q', 'Z'])
        self.assertTrue(player.test_word('AM'))