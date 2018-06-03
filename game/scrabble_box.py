"""
This contains the elements of the scrabble box: the board, the tiles, the rule book, and the dictionary
"""
from collections import Counter
from game.exceptions import InvalidCoordinatesError, InvalidPlacementError, InvalidWordError, OutOfBoardError

import colorama
import json
import random
import sys
import string

class Board(object):
    def __init__(self):
        # List of strings used just in checking for special tiles later on.
        self.board_special_tiles = [
            'W  l   W   l  W',
            ' w   L   L   w ',
            'l  w   l   w  l',
            '    w     w    ',
            ' L   L   L   L ',
            '  l   l l   l  ',
            'W  l   *   l  W',
            '  l   l l   l  ',
            ' L   L   L   L ',
            '    w     w    ',
            'l  w   l   w  l',
            ' w   L   L   w ',
            'W  l   W   l  W',
        ]
        # The board on which the tiles will actually be placed.
        self.board = [['_' for _ in range(15)] for _ in range(15)]
        with open('docs/tile_scores.json', 'r') as infile:
            self.tile_scores = json.load(infile)

    def __str__(self):
        """
        :return: A board showing the currently played tiles.
        """
        string_rep = "   " + ' '.join([str(hex(x))[-1] for x in range(15)]) + "\n"
        for i in range(15):
                string_rep += str(hex(i))[-1] + '  ' + ' '.join([self.board[i][j] for j in range(15)]) + '\n'
        return string_rep

    def place_word(self, word, coords, dir, tiles):
        """
        Places a word on the board, if valid
        :param word: The word to be placed, including both the tiles of the player and the tiles on the board.
        :param coords: The coords at which the first letter of the word will be placed
        :param dir: the direction, either down or right, from this first word in which the remainder will move.
        :param tiles: The rack of the player's tiles, checking that the word uses the correct tiles
        :return: None
        :raises InvalidCoordinatesError:
        :raises InvalidPlacementError:
        """

        def invalid_words():
            """
            Checks that the placed words, as well as other words formed by it being adjacent to other tiles, are
            valid.
            :return: A list of all invalid words created
            """
            # TODO: Complete function.
            pass

        # Check the coordinates are valid
        if not max(coords) < 15 and min(coords) > 0:
            raise InvalidCoordinatesError()
        if (dir == 'D' and coords[1] + len(word) > 14) or (dir == 'R' and coords[0] + len(word) > 14):
            raise InvalidPlacementError(word)

        # TODO: Check word actually fits in this spot, and tiles provided and tiles on board are enough to compelete it.

        # Now that we know that the placement is valid, we'll check the



class Bag(object):
    """ The bag of tiles from which pieces are pulled. """
    def __init__(self):
        """
        This dictionary will be used by the bots in determining the probability of pulling a favorable piece
        from the bag, and thus whether it is best to play a poor word or switch it for a better opportunity.
        """
        with open('docs/tile_counts.json', 'r') as infile:
            self.tile_counts = json.load(infile)

        self.bag = []
        for letter, count in self.tile_counts.items():
            self.bag += [letter for _ in range(count)]

    def __str__(self):
        """
        Displays the contents of the bag, used in debugging purposes.
        :return: A string form of a dictionary containing the number of occurrences of each word.
        """
        counts = Counter(self.bag).items()
        counts = sorted(counts, key=lambda x: x[0])
        # Just move the ? to the end for clarity, as Python interprets it as coming before A
        counts = counts[1:] + counts[:1]
        return ', '.join([letter + ': ' + str(count) for letter, count in counts])

    def grab(self, num_tiles):
        """
        :param num_tiles: Num tiles attempted to be removed
        :return: num_tiles from bag if available, otherwise as many as remain in the bag.
        """

        """ 
        While we could shuffle the bag on creation and it'd make no statistical difference and waste a little
        less computational energy, it just feels more authentic to the scrabble experience to shuffle each time.
        """
        random.shuffle(self.bag)

        # If there are not enough tiles in the bag, we just take what's available.
        num_tiles = min(num_tiles, len(self.bag))

        # Pull the requested tiles and update the bag.
        new_tiles, self.bag = self.bag[:num_tiles], self.bag[num_tiles:]
        return new_tiles

    def switch(self, discarded_tiles):
        """
        :param discarded_tiles: A list of single-character strings representing the tiles to be discarded.
        :return: A replacement number of tiles if available, or the original tiles if the switch cannot be made.
        """

        # In scrabble, tiles cannot be exchanged if there are seven or fewer tiles in the bag.
        if len(self.bag) <= 7:
            sys.stderr.write("ERROR: Tiles can only be exchanged when there are more than 7 tiles in the bag.")
            return discarded_tiles

        # Otherwise, we'll grab the requisite tiles from the bag and reinsert our current tiles.
        new_tiles = self.grab(len(discarded_tiles))
        self.bag += discarded_tiles

        return new_tiles

if __name__ == '__main__':
    board = Board()
    bag = Bag()
    print(bag)