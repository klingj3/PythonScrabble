"""
This contains the elements of the scrabble box: the board, the tiles, the rule book, and the dictionary
"""
from collections import Counter
from game.exceptions import InvalidCoordinatesError, InvalidPlacementError, InvalidWordError, OutOfBoardError
from game.scrabble_players import AIPlayer, HumanPlayer

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
            '  w   l l   w  ',
            'l  w   l   w  l',
            '    w     w    ',
            ' L   L   L   L ',
            '  l   l l   l  ',
            'W  l   *   l  W',
            '  l   l l   l  ',
            ' L   L   L   L ',
            '    w     w    ',
            'l  w   l   w  l',
            '  w   l l   w  ',
            ' w   L   L   w ',
            'W  l   W   l  W',
        ]
        # The board on which the tiles will actually be placed.
        self.board = [''.join([' ' for _ in range(15)]) for _ in range(15)]
        with open('docs/tile_scores.json', 'r') as infile:
            self.tile_scores = json.load(infile)

    def __str__(self):
        """
        :return: A board showing the currently played tiles.
        """
        string_rep = "   " + ' '.join([str(hex(x))[-1] for x in range(15)]) + "\n"
        for i in range(15):
            string_rep += str(hex(i))[-1] + '  ' + ' '.join([self.board[i][j] if self.board[i][j] != ' ' else
                                                             self.board_special_tiles[i][j] for j in range(15)]) + '\n'
        return string_rep

    def place_word(self, word, coords, dir):
        """
        Places a word on the board, if valid
        :param word: The word to be placed, including both the tiles of the player and the tiles on the board.
        :param coords: The coords at which the first letter of the word will be placed
        :param dir: the direction, either down or right, from this first word in which the remainder will move.
        :return: None
        """

        coord_x, coord_y = coords
        if dir == 'D':
            for i, c in enumerate(word):
                self.board[coord_y+i][coord_x] = c
        if dir == 'R':
            for i, c in enumerate(word):
                self.board[coord_y][coord_x+i] = c


class GameMaster(object):
    """
    It is the role of the GameMaster to act as the intermediary between the players and the game pieces. It keeps
    track of the score, checks for rule violations, and generally acts as an error-checking buffer.

    It is also responsible for the creation of players, and cycling through them at appropriate intervals.
    """

    def __init__(self, human_count=0, ai_count=0):
        """
        :param human_count: The number of human players to be
        :param ai_count: The number of AI players.
        """
        # Generate the game pieces.
        self.board = Board()
        self.bag = TileBag()

        self.players = []
        for i in range(human_count):
            self.players.append(HumanPlayer(id=i, init_tiles=self.bag.grab(7)))
        for i in range(ai_count):
            self.players.append(AIPlayer(id=human_count+i, init_tiles=self.bag.grab(7), name="AI {}".format(i+1)))

    def play_game(self):
        """
        Cycle through the players in the list, prompting them for their individual moves until the game is over.
        :return: None
        """

        # We keep track of the consecutive skips as this is one of the conditions which can lead to the game's end.
        consecutive_skips = 0

        player_count = len(self.players)

        # The game ends when oen player has used all of their tiles, or if everyone skips for two turns because nothing
        # can be placed. (This is very unlikely, but must be included as an edge case.
        while consecutive_skips < 2*player_count or min([len(player.tiles()) for player in self.players]) == 0:
            for player in self.players:
                # On each player's turn we'll print the board, the scores, and the active player's tiles.
                # TODO: Beautify Command-line appearance
                print(self.board)
                print('TURN: {}'.format(player.name))
                exit()


class TileBag(object):
    """ The bag of tiles from which pieces are pulled. """
    def __init__(self):
        """
        This dictionary will be used by the bots in determining the probability of pulling a favorable piece
        from the bag, and thus whether it is best to play a poor word or switch it for a better opportunity.
        """
        with open('docs/tile_counts.json', 'r') as infile:
            self.tile_counts = json.load(infile)

        # Use these counts to generate the correct numbers of tiles in the bag.
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

