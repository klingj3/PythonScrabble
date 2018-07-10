from collections import namedtuple
from scrabble_box import RuleBook

import sys

# TODO: REMOVE DEBUG STATEMENTS
debug_mode = True

class Player(object):
    def __init__(self, id, init_tiles, name=None):
        while name is None:
            name = input("Enter the name for this player: ")
            if name.isspace():
                print('Player names must contain non-space characters.')
                name = None
        self.name = name
        self.id = id
        """
        We'll save score and word histories. While a score history doesn't have any particular utility, it's more true
        to Scrabble tradition and style than just having the current score. Word histories are important to save 
        so that analysis can be completed after the game is completed, possibly to tune the parameters of the AI in
        later incarnations.  
        """
        self.score_hist = []
        self.word_hist = []
        self.tiles = init_tiles
        assert(len(self.tiles) == 7)

    def __str__(self):
        return self.name

    def get_score(self):
        return self.score_hist[-1]

    def recieve_tiles(self, new_tiles):
        """
        Used for the game master to pass new tiles to a player after said player has made a move
        :param new_tiles: A list of single-character strings representing the tiles
        :return: None
        """
        self.tiles += new_tiles
        if debug_mode:
            # Check that too many tiles haven't been given. As late-game enables a player to have fewer than seven
            # tiles, we must allow for that scenario in this test despite its rarity.
            assert(len(self.tiles) <= 7)

    def prompt_move(self, board_state):
        """
        :param board_state: The current board
        :return: A string representing the player's desired move, or a reordering of the tiles.
        """
        pass

    def set_tiles(self, tiles):
        self.tiles = tiles


class HumanPlayer(Player):
    """
    This is a class for a human player to interact with the scrabble board directly, interacting with the
    Game Master through the command line/terminal interface.
    """
    def __init__(self, id, init_tiles, name=None):
        Player.__init__(self, id, init_tiles, name)

    def prompt_move(self, board_state):
        """
        :param board_state: The current board
        :return: A string representing the player's desired move. ALl error checking regarding the legality of this
                move and string integrity is handled by the game-master.
        """
        return input("Action: ")


class AIPlayer(Player):
    """
    AI Competitor
    """
    def __init__(self, id, init_tiles, rulebook, name=None):
        # Call the default constructor to set name and tiles
        Player.__init__(self, id, init_tiles, name="AI {}".format(id))

        # The rulebook for scoring moves and other similar functions
        self.rulebook = rulebook

        # Build our scrabble dictionary, and the tree for quickly finding words in this dictionary
        """
        While in the current incarnation of this project, it is a little redundant to have a scrabble dictionary exist
        within each AI as well as within the rulebook, in future incarnations the dictionary will be dependent on 
        difficulty options, so this redundancy is for now included in order to facilitate this advancement down 
        the line.
        """
        self.dictionary_root, self.scrabble_dictionary = self.rulebook.generate_dictionary_tree()

    def find_words(self, tiles=None, starting_branch=None, req_tiles=[], pos=0, min_length=2, max_length=15):
        """
        :param tiles: A list of single-characters representing the player's tiles.
        :param starting_branch: The starting branch in the dictionary tree which we'll be exploring
        :param req_tiles: A list of tuples containing a character and the zero-indexed position in the created word
        in which the tile must occur. For example, if the second letter of the word must be 'A' and the third
        letter of the word must be 'M', this variable would be [('A',1), ('M',2)].
        :param pos: The current position in the word.
        :param max_length: The longest a generated word can be, dictated by the coordinates on which the first tile
        will be placed.
        :return: A list of valid words which can be formed using the tiles in the rack and with the mandated positions
        of the tiles given.
        """
        if pos == max_length:
            return []

        if tiles is None:
            tiles = self.tiles.copy()
        if starting_branch is None:
            starting_branch = self.dictionary_root

        # We must check that the mandated tiles are in their correct order.
        # TODO: Remove this function once the AI is complete and this condition is unnecessary
        assert(len(req_tiles) == 1 or
               all([req_tiles[i][1] < req_tiles[i + 1][1] for i in range(len(req_tiles) - 1)]))

        def without(full_list, item):
            """
            A shorthand for creating a copy of a list sans the first occurrence of an element, since most times we
            recur we'll remove one element from the tile rack.
            :param full_list: A list of objects
            :param item: Item to be removed
            :return: A copy of the list with the item removed.
            """
            local_list = full_list.copy()
            if item in local_list:
                local_list.remove(item)
            return local_list

        if starting_branch['VALID'] and len(starting_branch['WORD']) >= min_length:
            valid_words = [starting_branch['WORD']]
        else:
            valid_words = []

        # If our current position features a mandated tile, then we check to see if that's a valid entry at this point
        # in the tree
        if req_tiles and req_tiles[0][1] == pos:
            if req_tiles[0][0] in starting_branch:
                valid_words += self.find_words(tiles, starting_branch[req_tiles[0][0]], req_tiles[1:], pos=pos+1)
        else:
            # Casting tile to a set ensures we don't doubly traverse a branch in the case of repeated letters.
            for tile in set(tiles):
                if tile != '?':
                    if tile in starting_branch:
                        valid_words += self.find_words(without(tiles, tile), starting_branch[tile], pos=pos+1)
                else:
                    # In the case of blank tiles, we traverse every branch
                    words_with_blanks = []
                    for key, value in starting_branch.items():
                        if key != 'VALID' and key != 'WORD':
                            words_with_blanks += self.find_words(without(tiles, '?'), starting_branch[tile], pos=pos+1)
                    # For the sake of scoring, we replace the character used in place of blank for traversal with a '?'
                    words_with_blanks = [word[:pos] + '?' + word[pos+1:] for word in words_with_blanks]
                    valid_words += words_with_blanks
        return valid_words

    def get_valid_locations(self, board_state):
        """
        :return: A list of "MoveParam" named tuples, containing the coordinates, orientation, min word length
        and max word length for perspective moves.
        """

        MoveParam = namedtuple('MoveParam', 'coords dir min max fixed')

        def move_params_from_coords(coords, dir, num):
            """
            Asserts that the number of tiles can be placed in the direction dir with the coordinates coords.
            Returns the (zero indexed) number of tiles until this becomes valid, and the ultimate length of the move. For example,
            if we're trying to place five tiles across line '_ _ A _ _ _ _ _ _ _ _ _ _ _ _ ' from the first
            position, the result would be (2, 6, [(2, A)] as it becomes valid at tile 2 and the maximum number of letters
            in the result will be six.
            :param coords: y and x integer coordinates in tuple
            :param dir: string 'D' or 'R' for down or right.
            :param num: The number of tiles being placed.
            :return: tuple (int, int, list)
            """

            def is_island(y, x):
                """
                Checks to see if the given coordinate is an island in scrabble terms, meaning that there is no tile
                directly above, below, to the left, or to the right of it, though diagonals are of course still valid.
                :param y: Integer Y coordinate
                :param x: Integer X coordinate
                :return: True if the coordinates has no existing tile on any side.
                """
                # All first moves will be an island, but we'll of return false so the game can begin.
                if (y, x) == (7, 7):
                    return False

                min_x, max_x = max(x - 1, 0), min(x + 1, len(board_state[0]))
                min_y, max_y = max(y - 1, 0), min(y + 1, len(board_state))
                for neighbor_y in range(min_y, max_y + 1):
                    if board_state[neighbor_y][x] != ' ':
                        return False
                for neighbor_x in range(min_x, max_x+1):
                    if board_state[y][neighbor_x] != ' ':
                        return False
                return True

            # TODO: remove assertions used in testing
            assert (dir == 'D' or dir == 'R')
            start_y, start_x = coords
            y, x = coords
            fixed_tiles = []
            tiles_rem = num
            tiles_to_validity = -1
            if dir == 'D':
                while tiles_rem:
                    if y >= 15:
                        return tiles_to_validity, y-start_y, fixed_tiles
                    if tiles_to_validity == -1:
                        if not is_island(y, x):
                            tiles_to_validity = y - start_y
                    if board_state[y][x] == ' ':
                        tiles_rem -= 1
                    else:
                        fixed_tiles.append((y-start_y, board_state[y][x]))
                    y += 1
                return tiles_to_validity, (y - start_y), fixed_tiles
            else:
                while tiles_rem:
                    if x >= 15:
                        return tiles_to_validity, x-start_x, fixed_tiles
                    if tiles_to_validity == -1:
                        if not is_island(y, x):
                            tiles_to_validity = x - start_x
                    if board_state[y][x] == ' ':
                        tiles_rem -= 1
                    else:
                        fixed_tiles.append((x-start_x, board_state[y][x]))
                    x += 1
                return tiles_to_validity, (x - start_x), fixed_tiles

        valid_move_params = []
        num = len(self.tiles)

        # Check moves for the down direction
        for y in range(15 - num):
            for x in range(15):
                min_len, max_len, fixed_tiles = move_params_from_coords((y, x), 'D', num)
                if min_len != -1:
                    valid_move_params.append(MoveParam((y, x), 'D', min_len, max_len, fixed_tiles))

        # Check moves for the right direction.
        for y in range(15):
            for x in range(15 - num):
                min_len, max_len, fixed_tiles = move_params_from_coords((y, x), 'R', num)
                if min_len != -1:
                    valid_move_params.append(MoveParam((y, x), 'R', min_len, max_len, fixed_tiles))

        return valid_move_params

    def prompt_move(self, board_state):
        """
        :param board_state: A 15 by 15 grid reflecting the current placement of tiles on the board.
        :return:
        """

        """
        First, we look at all the positions on the board and determine which coordinates can be the starting position 
        for a word, the minimum length of a word which adheres to the placement rules of scrabble, and the maximum 
        length of a word formed this point.
        """
        valid_locations = self.get_valid_locations(board_state)

        """
        Knowing where we can place words and how long the words can be moved, as well as what tiles this move would
        be forced to incorporate, we can find what valid words we can play.
        """
        valid_moves = []
        Move = namedtuple('move', 'coords dir word')
        for vl in valid_locations:
            valid_words = self.find_words(req_tiles=vl.fixed, min_length=vl.min, max_length=vl.max)
            valid_moves += [Move(vl.coords, vl.dir, word) for word in valid_words]
