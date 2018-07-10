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
        self.board = [''.join([' ' for _ in range(15)]) for _ in range(15)]

    def __str__(self):
        """
        :return: A board showing the currently played tiles.
        """
        string_rep = "   " + ' '.join([str(hex(x))[-1] for x in range(15)]) + "\n"
        for i in range(15):
            # TODO: USE COLOR TOOLS TO MAKE DISPLAY SPECIAL TILES DIFFERENT AND MAKE THEM DIFFERENT COLOR
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

    def score_word(self, y, x, word, dir, board_state, allow_illegal=False):
        """
        :param y: Starting y coordinate
        :param x: starting x coordinate
        :param word: The word being played, new tiles as well as (potentially) existing board tiles.
        :param dir: 'R' or 'D' representing the direction in which the word is moving.
        :param board_state: A list of 15 strings of 15 characters representing the current state of the board.
        :param allow_illegal: If False, returns -1 i the word is not in the dictionary. Otherwise, scores
        the word as if it was entirely valid.
        :return: Integer score of the word
        """
        if dir == 'R':
            # Process the word in the right direction
            score = 0
            word_mul = 1
            for i, tile in enumerate(word):
                # If the character exists on the board at this point, then the tile has already been played.
                if board_state[y][x+i] != ' ':
                    if board_state[y][x+i] != tile:
                        # The character on the board at this point does not match the tile which should exist in the word.
                        raise InvalidPlacementError(word)
                    else:
                        score += self.tile_scores[tile]
                else:
                    # The board is blank at this point, meaning that the special tile markers contribute to its score.
                    if self.board_special_tiles[y][x+i] == ' ':
                        score += self.tile_scores[tile]
                    else:
                        if self.board_special_tiles[y][x+i] == 'l':
                            score += self.tile_scores[tile]*2
                        elif self.board_special_tiles[y][x+i] == 'L':
                            score += self.tile_scores[tile]*3
                        else:
                            # Otherwise, tile is a word multiplier.
                            if self.board_special_tiles[y][x+i] == 'W':
                                word_mul *= 3
                            else:
                                # TODO: Remove ancillary debug statement
                                assert(self.board_special_tiles[y][x+i] in 'W*')
                                word_mul *= 2
        if dir == 'D':
            # Process the word in the right direction
            score = 0
            word_mul = 1
            for i, tile in enumerate(word):
                # If the character exists on the board at this point, then the tile has already been played.
                if board_state[y+i][x] != ' ':
                    if board_state[y+i][x] != tile:
                        # The tile does not match the tile which should exist in the word.
                        raise InvalidPlacementError(word)
                    else:
                        score += self.tile_scores[tile]
                else:
                    # The board is blank at this point, meaning that the special tile markers contribute to its score.
                    if self.board_special_tiles[y+i][x] == ' ':
                        score += self.tile_scores[tile]
                    else:
                        if self.board_special_tiles[y+i][x] == 'l':
                            score += self.tile_scores[tile]*2
                        elif self.board_special_tiles[y+i][x] == 'L':
                            score += self.tile_scores[tile]*3
                        else:
                            # Otherwise, tile is a word multiplier.
                            if self.board_special_tiles[y+i][x] == 'W':
                                word_mul *= 3
                            else:
                                # TODO: Remove ancillary debug statement
                                assert(self.board_special_tiles[y+i][x] in 'W*')
                                word_mul *= 2
        # TODO: Remove ancillary debug if never reached in testing.
        else:
            raise ValueError('ERROR: Direction other than R and D provided.')

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
        :param move: namedtuple containing ('move', 'coords', 'dir', 'word')
        :param board_state: List of strings representing the current board condition
        :return: Score
        :rtype int
        """

        def neighbored_x(y, x):
            return (x > 0 and board_state[y][x-1] != ' ') or (x < 14 and board_state[y][x+1] != ' ')

        def neighbored_y(y, x):
            return (y > 0 and board_state[y-1][x] != ' ') or (y < 14 and board_state[y+1][x] != ' ')

        if not self.word_is_valid(move.word):
            return 0

        total_score = self.score_word(move.coords[0], move.coords[1], move.word, move.dir, board_state)

        start_y, start_x = move.coords
        if move.dir == 'D':
            for i, y in enumerate(range(start_y, (len(move.word)+start_y))):
                if neighbored_x(y, start_x):
                    word_start, word_end = start_x, start_x
                    while word_start > 0 and board_state[y][word_start - 1] != ' ':
                        word_start -= 1
                    while word_end < 14 and board_state[y][word_end + 1] != ' ':
                        word_end += 1
                    anc_word = board_state[y][word_start:start_x] + move.word[i] + board_state[y][start_x+1:word_end+1]

                    # TODO: Remove debug statements
                    if debug_mode:
                        print(anc_word + ' ' + str(anc_word in self.scrabble_dictionary))

                    if self.word_is_valid(anc_word):
                        total_score += self.score_word(y, word_start, anc_word, 'R', board_state)
                    else:
                        return 0

            return True
        else:
            for i, x in enumerate(range(start_x, (len(move.word)+start_x))):
                if neighbored_y(start_y, x):
                    word_start, word_end = start_y, start_y
                    while word_start > 0 and board_state[word_start - 1][x] != ' ':
                        word_start -= 1
                    while word_end < 14 and board_state[word_end + 1][x] != ' ':
                        word_end += 1
                    anc_word = ''.join([board_state[word_y][x] if word_y != start_y else move.word[i]
                                        for word_y in range(word_start, word_end+1)])

                    # TODO: Remove debug statements
                    if debug_mode:
                        print(anc_word + ' ' + str(anc_word in self.scrabble_dictionary))

                    if self.word_is_valid(anc_word):
                        total_score += self.score_word(word_start, x, anc_word, 'D', board_state)
                    else:
                        return 0
            return True

    def word_is_valid(self, word):
        def check_tree(branch, pos=0):
            if pos >= len(word):
                return True
            char = word[pos]
            if char == '?':
                return any([check_tree(branch[value], pos+1) for key, value in branch
                            if key != 'VALID' and key != 'WORD' for key, value in branch.items()])
            else:
                if char in branch:
                    return check_tree(branch[char], pos+1)
                else:
                    return False

        # If there is no blank tile, we simply assert that the word is in our dictionary
        if '?' not in word:
            return word in self.scrabble_dictionary
        else:
            return check_tree(self.dictionary_root)


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

