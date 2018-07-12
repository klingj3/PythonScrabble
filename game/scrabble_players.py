from collections import namedtuple
from game.scrabble_box import Rulebook

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
        # assert(len(self.tiles) == 7)

    def __str__(self):
        return self.name

    def get_move(self, board_state):
        """
        :param board_state: A list of strings reprenting the currently played tiles on the scrabble board.
        :return: A namedtuple Move defined as ('Move', 'coords word dir')
        :rtype namedtuple
        """
        pass

    def prompt_move(self, board_state):
        """
        :param board_state: The current board
        :return: A Tuple containing the Move namedtuple the player is performing.
        """

        def remove_used_tiles(move):
            coords, word, dir = move.coords, move.word, move.dir
            is_d, is_r = (dir == 'D', dir == 'R')
            y, x = coords
            for i, tile in enumerate(word):
                # If the board is blank at this point, remove the tile from our tiles.
                if board_state[y + i * is_d][x + i * is_r] == ' ':
                    if tile.islower():
                        tile = '?'
                    self.tiles.remove(tile)

        # Get the next move
        move = self.get_move(board_state)

        # Remove the tiles from the bag.
        remove_used_tiles(move)

        return move

    def receive_tiles(self, new_tiles):
        """
        Recieve new tiles after a successfully played turn.
        :param new_tiles: A list of single-character strings representing the Tiles.
        :return: None
        """
        self.tiles += new_tiles

        if debug_mode:
            assert (len(self.tiles) <= 7)

    def set_tiles(self, tiles):
        """
        Used for the Game Master to set the player's tiles for debugging purposes.
        :param tiles: The list of single character strings representing the new tiles.
        :return: None
        """
        if not debug_mode:
            sys.stderr.write('SET TILES TO BE USED ONLY IN DEBUG MODE.')

        self.tiles = tiles

        if debug_mode:
            assert (len(self.tiles) <= 7)


class HumanPlayer(Player):
    """
    This is a class for a human player to interact with the scrabble board directly, interacting with the
    Game Master through the command line/terminal interface.
    """

    def __init__(self, id, init_tiles, name=None):
        Player.__init__(self, id, init_tiles, name)

    def get_move(self, board_state):
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

    def __init__(self, id, init_tiles, name=None):
        # Call the default constructor to set name and tiles
        Player.__init__(self, id, init_tiles, name="AI {}".format(id))

        # The rulebook for scoring moves and other similar functions
        self.rulebook = Rulebook()

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
        :param min_length: The shortest a generated word can be, dictated by the number of tiles until a played piece
        borders an existing piece on the board.
        :param max_length: The longest a generated word can be, dictated by the coordinates on which the first tile
        will be placed.
        :return: A list of valid words which can be formed using the tiles in the rack and with the mandated positions
        of the tiles given.
        """
        if pos > max_length:
            return []

        if tiles is None:
            tiles = self.tiles.copy()
        if starting_branch is None:
            starting_branch = self.dictionary_root

        assert (len(req_tiles) == 1 or
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

        if starting_branch['VALID'] and len(starting_branch['WORD']) >= min_length and len(tiles) < len(self.tiles):
            valid_words = [starting_branch['WORD']]
        else:
            valid_words = []

        # If our current position features a mandated tile, then we check to see if that's a valid entry at this point
        # in the tree
        if req_tiles and req_tiles[0][1] == pos:
            if req_tiles[0][0] in starting_branch:
                valid_words += self.find_words(tiles=tiles,
                                               starting_branch=starting_branch[req_tiles[0][0]],
                                               req_tiles=req_tiles[1:],
                                               pos=pos + 1,
                                               min_length=min_length,
                                               max_length=max_length)
        else:
            # Casting tile to a set ensures we don't doubly traverse a branch in the case of repeated letters.
            for tile in set(tiles):
                if tile != '?':
                    if tile in starting_branch:
                        valid_words += self.find_words(tiles=without(tiles, tile),
                                                       starting_branch=starting_branch[tile],
                                                       pos=pos + 1,
                                                       min_length=min_length,
                                                       max_length=max_length,
                                                       req_tiles=req_tiles)
                else:
                    # In the case of blank tiles, we traverse every branch
                    words_with_blanks = []
                    for key, value in starting_branch.items():
                        if key != 'VALID' and key != 'WORD':
                            words_with_blanks += self.find_words(tiles=without(tiles, '?'),
                                                                 starting_branch=starting_branch[key],
                                                                 pos=pos + 1,
                                                                 min_length=min_length,
                                                                 max_length=max_length,
                                                                 req_tiles=req_tiles)
                    words_with_blanks = [word[:pos] + word[pos].lower() + word[pos + 1:] for word in words_with_blanks]
                    valid_words += words_with_blanks
        return valid_words

    def get_valid_locations(self, board_state):
        """
        :return: A list of "MoveParam" named tuples, containing the coordinates, orientation, min word length
        and max word length for perspective moves.
        """

        MoveParam = namedtuple('MoveParam', 'coords dir min max fixed')

        def move_params_from_coords(coords, direction, num):
            """
            Asserts that the number of tiles can be placed in the direction dir with the coordinates coords.
            Returns the (zero indexed) number of tiles until this becomes valid, and the ultimate length of the move.
            For example, if we're trying to place five tiles across line '_ _ A _ _ _ _ _ _ _ _ _ _ _ _ ' from the first
            position, the result would be (2, 6, [(2, A)] as it becomes valid at tile 2 and the maximum number of
            letters in the result will be six.
            :param coords: y and x integer coordinates in tuple
            :param direction: string direction 'D' or 'R' for down or right.
            :param num: The number of tiles being placed.
            :return a tuple containing the minimum word length, maximum word length, and the locations in the word of
            preplaced tiles.
            :rtype tuple (int, int, list)
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

                min_x, max_x = max(x - 1, 0), min(x + 1, 14)
                min_y, max_y = max(y - 1, 0), min(y + 1, 14)
                for near_y in range(min_y, max_y + 1):
                    if board_state[near_y][x] != ' ':
                        return False
                for near_x in range(min_x, max_x + 1):
                    if board_state[y][near_x] != ' ':
                        return False
                return True

            # TODO: remove assertions used in testing
            assert (direction == 'D' or direction == 'R')
            start_y, start_x = coords
            y, x = coords
            fixed_tiles = []
            tiles_rem = num

            tiles_to_validity = -1

            if direction == 'D':
                while tiles_rem:
                    if y >= 15:
                        return tiles_to_validity, y - start_y, fixed_tiles
                    if tiles_to_validity == -1:
                        if not is_island(y, x):
                            tiles_to_validity = y - start_y + 1
                    if board_state[y][x] == ' ':
                        tiles_rem -= 1
                    else:
                        fixed_tiles.append((board_state[y][x], y - start_y))
                    y += 1
                return tiles_to_validity, (y - start_y + 1), fixed_tiles
            else:
                while tiles_rem:
                    if x >= 15:
                        return tiles_to_validity, x - start_x, fixed_tiles
                    if tiles_to_validity == -1:
                        if not is_island(y, x):
                            tiles_to_validity = x - start_x + 1
                    if board_state[y][x] == ' ':
                        tiles_rem -= 1
                    else:
                        fixed_tiles.append((board_state[y][x], x - start_x))
                    x += 1
                return tiles_to_validity, (x - start_x + 1), fixed_tiles

        valid_move_params = []
        num = len(self.tiles)

        # Check moves for the down direction
        for y in range(15):
            for x in range(15):
                min_len, max_len, fixed_tiles = move_params_from_coords((y, x), 'D', num)
                if min_len != -1:
                    valid_move_params.append(MoveParam((y, x), 'D', min_len, max_len, fixed_tiles))

        # Check moves for the right direction.
        for y in range(15):
            for x in range(15):
                min_len, max_len, fixed_tiles = move_params_from_coords((y, x), 'R', num)
                if min_len != -1:
                    valid_move_params.append(MoveParam((y, x), 'R', min_len, max_len, fixed_tiles))

        return valid_move_params

    def get_move(self, board_state):

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
        Move = namedtuple('move', 'coords dir word')

        valid_moves = []
        for vl in valid_locations:
            if vl.coords == (0, 7):
                print(vl)
            valid_words = self.find_words(req_tiles=vl.fixed, min_length=vl.min, max_length=vl.max)
            valid_moves += [Move(vl.coords, vl.dir, word) for word in valid_words]

        # Now we score our prospective moves, and remove the invalid ones.
        move_scores = [(move, self.rulebook.score_move(move, board_state)) for move in valid_moves
                       if self.rulebook.score_move(move, board_state) > 0]

        move_scores = sorted(move_scores, key=lambda x: x[1], reverse=True)

        if debug_mode:
            print(self.tiles)
            print('WAZZZIII')
            top_scores = move_scores[:3]
            for move, score in top_scores:
                print("Word {} for {} points, from coords {} {}".format(move.word, score, move.coords[0],
                                                                        move.coords[1]))
            sys.stdout.flush()
        move, score = move_scores[0]
        return move
