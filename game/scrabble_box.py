"""
This contains the elements of the scrabble box: the board, the tiles, the rule book, and the dictionary
"""
from collections import Counter
from game.exceptions import InvalidCoordinatesError, InvalidPlacementError, InvalidWordError, OutOfBoardError

import json
import random
import sys

# TODO: Remove debugs once the final tests are completed.
debug_mode = False


class Board(object):
    def __init__(self):
        # The special tiles.
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
        self.state = [''.join([' ' for _ in range(15)]) for _ in range(15)]

    def __str__(self):
        """
        :return: A board showing the currently played tiles.
        """
        string_rep = "   " + ' '.join([str(hex(x))[-1] for x in range(15)]) + "\n"
        for i in range(15):
            # TODO: USE COLOR TOOLS TO MAKE DISPLAY SPECIAL TILES DIFFERENT AND MAKE THEM DIFFERENT COLOR
            string_rep += str(hex(i))[-1] + '  ' + ' '.join([self.state[i][j] for j in range(15)]) + '\n'
        return string_rep

    def play_move(self, move):
        y, x = move.coords
        if move.dir == 'D':
            for i, c in enumerate(move.word):
                self.state[y + i] = self.state[y + i][:x] + c + self.state[y + i][x+1:]
        if move.dir == 'R':
            self.state[y] = self.state[y][:x] + move.word + self.state[y][x+len(move.word):]
        return True


class Rulebook(object):
    """Contains the rule checking functions, special tile info, and other such functions."""
    def __init__(self):
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

        with open('docs/tile_scores.json', 'r') as infile:
            self.tile_scores = json.load(infile)
        self.dictionary_root, self.scrabble_dictionary = self.generate_dictionary_tree()

    @staticmethod
    def generate_dictionary_tree():
        """
        Rather than having a huge list to traverse through, or a set to check against, the dictionary of this agent
        is stored through a series of nested dictionaries, which work like a tree with easier indexing. Each branch of
        this tree contains at least two values in its initial dictionary, WORD which is the word up to that point in
        the tree (a little expensive on memory, but the whole dictionary isn't so large by modern standards), and VALID
        which is if the current word is valid or not. For example, the word 'MAZE' would be found by traversing through
        the tree as follows:

        '' -> M (WORD=M,VALID=FALSE) -> A (WORD=MA,VALID=TRUE) -> Z (WORD=MAZ,VALID=FALSE) -> E (WORD=MAZE,VALID=TRUE)

        Of course, this is a simplified view, as that first M doesn't point only to A, but to every letter for which
        there exists a word where the first letter is M and the second letter is that letter in question. I'm still
        examining faster solutions, but at the moment it has been quite successful as a mode for discovering anagrams.

        :return: Tuple (Dir tree, set of all words)
        :rtype: Tuple
        """

        # While on paper it'd make more sense to write and load this file from a saved dictionary tree, in actuality
        # loading it only takes a fraction of a second less time than creating it, so since this method is only called
        # on game initialization it's better to generate it fresh and have one fewer file to force the user to download.

        # We build a tree from this dictionary of words.
        dictionary_tree = {'VALID': False, 'WORD': ''}
        with open("docs/dictionary.txt") as dict_file:
            dictionary_lines = [word.replace('\n', '') for word in dict_file]

        for word in dictionary_lines:
            active_branch = dictionary_tree
            for i, character in enumerate(word):
                if character not in active_branch:
                    active_branch[character] = {'VALID': False, 'WORD': active_branch['WORD'] + character}
                active_branch = active_branch[character]
                if i == len(word) - 1:
                    active_branch['VALID'] = True
        return dictionary_tree, set(dictionary_lines)

    def score_move(self, move, board_state, allow_illegal=False):
        """
        Check that the ancillary words formed are also valid, and returns the score of the move if all words are valid.
        For example starting with the small board
        _ _ _
        _ D _
        _ O _
        _ G _

        If we play the word "Ram" at 2, 0 Down, we'll create the board
        _ _ R
        _ D A
        _ O M
        _ G _
        And must then check that DA and OM are valid (They are), and then score the move.
        Returns 0 if the move is invalid.
        :param move: namedtuple defined as as ('move', 'coords dir word')
        :param board_state: List of strings representing the current board condition
        :return: Score
        :rtype int
        """

        def neighbored_x(y, x):
            return (x > 0 and board_state[y][x-1] != ' ') or (x < 14 and board_state[y][x+1] != ' ')

        def neighbored_y(y, x):
            return (y > 0 and board_state[y-1][x] != ' ') or (y < 14 and board_state[y+1][x] != ' ')

        assert(move.dir == 'R' or move.dir == 'D')

        y, x = move.coords

        total_score = self.score_word(y, x, move.word, move.dir, board_state, move)

        for i, tile in enumerate(move.word):
            if move.dir == 'D' and neighbored_x(y+i, x):
                # As the core word direction is down, we look for ancillary formed words along the X axis
                word_start, word_end = x, x
                while word_start > 0 and board_state[y+i][word_start - 1] != ' ':
                    word_start -= 1
                while word_end < 14 and board_state[y+i][word_end + 1] != ' ':
                    word_end += 1
                anc_word = board_state[y+i][word_start:x] + tile + board_state[y+i][x+1:word_end+1]

                if allow_illegal or self.word_is_valid(anc_word):
                    total_score += self.score_word(y+i, word_start, anc_word, 'R', board_state, move)
                else:
                    return -1
            elif neighbored_y(y, x+i):
                # As the core word direction is right, we look for ancillary formed words along the Y axis
                word_start, word_end = y, y
                while word_start > 0 and board_state[word_start - 1][x+i] != ' ':
                    word_start -= 1
                while word_end < 14 and board_state[word_end + 1][x+i] != ' ':
                    word_end += 1
                anc_word = ''.join([board_state[word_y][x+i] if word_y != y else tile
                                    for word_y in range(word_start, word_end+1)])

                if allow_illegal or self.word_is_valid(anc_word):
                    total_score += self.score_word(word_start, x+i, anc_word, 'D', board_state, move)
                else:
                    return -1

        return total_score

    def score_word(self, y, x, word, dir, board_state, move):
        """
        Scores a word played starting at coordinates x, y in direction dir.
        :param y: Starting y coordinate
        :param x: starting x coordinate
        :param word: The word being played, new tiles as well as (potentially) existing board tiles.
        :param dir: 'R' or 'D' representing the direction in which the word is moving.
        :param board_state: A list of 15 strings of 15 characters representing the current state of the board.
        :return: Integer score of the word
        :rtype int
        """

        score = 0
        word_mul = 1

        assert(dir == 'R' or dir == 'D')

        # Tracks the number of tiles the player has used in this word, as using all 7 is a 50 point bonus.
        player_tiles_used = 0

        # Instead of having an if statement for R and D with largely repeated contents, we can just add the
        # integer cast of the equality of the given direction to a particular direction.
        is_d, is_r = int(dir == 'D'), int(dir == 'R')

        for i, tile in enumerate(word):
            if tile.islower():
                tile = '?'

            # The current tile (or none) on the board at the current location.
            board_curr_tile = board_state[y+i*is_d][x+i*is_r]

            # Check to see if something has already been placed on the board.
            if board_curr_tile != ' ':
                if board_curr_tile != tile:
                    # The character on the board at this point does not match the tile which should exist in the word.
                    print(y, x, word, dir)
                    print(move)
                    raise InvalidPlacementError(word=word, true_tile=board_curr_tile, attempted_tile=tile)
                else:
                    score += self.tile_scores[tile]
            else:
                player_tiles_used += 1

                # Else, this is a fresh placed tile, in which case we look at the special value of this square
                spec_tile = self.board_special_tiles[y+i*is_d][x+i*is_r]
                if spec_tile == ' ':
                    score += self.tile_scores[tile]
                else:
                    if spec_tile == 'l':
                        score += self.tile_scores[tile]*2
                    elif self.board_special_tiles[y][x+i] == 'L':
                        score += self.tile_scores[tile]*3
                    else:
                        # Otherwise, tile is a word multiplier.
                        if spec_tile == 'W':
                            word_mul *= 3
                        else:
                            word_mul *= 2
        score *= word_mul
        if player_tiles_used == 7:
            score += 50
        return score

    def word_is_valid(self, word):
        # We cast the word to uppercase in case there's a blank tile in it.
        return word.upper() in self.scrabble_dictionary


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
