from collections import namedtuple
from game.scrabble_box import Rulebook
from game.exceptions import InvalidPlacementError

import sys

# TODO: REMOVE DEBUG STATEMENTS
debug_mode = False

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
        # The rulebook for scoring moves and other similar functions
        self.rulebook = Rulebook()

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

            # If this is an exchange move, then we don't need to check the contents of the board.
            if coords == (-2, -2):
                for tile in move.word:
                    self.tiles.remove(tile)
            else:
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

        # Check for the skip signal
        if move.coords != (-1, -1):
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

    def check_exchange_validity(self, discard_tiles):
        """
        Checks that the tiles desired to be exchanged exist on the player's rack, and so the exchange is valid.
        :param discard_tiles: A string of the tiles to be exchanged
        :return: True if valid, False otherwise.
        """
        rack = self.tiles.copy()
        for tile in discard_tiles:
            try:
                rack.remove(tile)
            except ValueError:
                return False
        return True

    def get_move(self, board_state):
        """
        :param board_state: The current board
        :return: A string representing the player's desired move. ALl error checking regarding the legality of this
                move and string integrity is handled by the game-master.
        """
        Move = namedtuple('move', 'coords dir word')
        while True:
            player_move = input("Action: ")
            move_segments = player_move.split(' ')

            if len(move_segments) == 1 and move_segments[0] == 'skip':
                return Move((-1, -1), '', '')
            elif len(move_segments) == 2 and move_segments[0] == 'exchange':
                if self.check_exchange_validity(move_segments[1]):
                    return Move((-2, -2), '', move_segments[1])
            elif len(move_segments) == 4:
                x, y, dir, word = move_segments
                move = Move((int(y, 16), int(x, 16)), dir, word)
                if move.coords[0] < 0 or move.coords[0] < 0 or move.coords[1] > 14 or move.coords[1] > 14:
                    print('Moves must be within the boundaries 0 and d (d being hexidecimal 14)')
                try:
                    move_score = self.rulebook.score_move(move, board_state)
                    if move_score < 0:
                        print('This word, or an ancillary word formed, is invalid.')
                    else:
                        return move
                except InvalidPlacementError:
                    print(InvalidPlacementError)
            else:
                print('Invalid Input.\n Moves must comprise of x coordinate, y coordinate, direction D or R, and the \
                        word to be played. To skip, type "skip", or to exchange tiles, type "exchange" followed by \
                        the tiles you wish to exchange'
                     )



class AIPlayer(Player):
    """
    AI Competitor
    """

    def __init__(self, id, init_tiles, name=None):
        # Call the default constructor to set name and tiles
        Player.__init__(self, id, init_tiles, name="AI {}".format(id))

        # Build our scrabble dictionary, and the tree for quickly finding words in this dictionary
        """
        While in the current incarnation of this project, it is a little redundant to have a scrabble dictionary exist
        within each AI as well as within the rulebook, in future incarnations the dictionary will be dependent on 
        difficulty options, so this redundancy is for now included in order to facilitate this advancement down 
        the line.
        """
        self.dictionary_root, self.scrabble_dictionary = self.rulebook.generate_dictionary_tree()

    def find_words(self, tiles=None, starting_branch=None, fixed_tiles=[], pos=0, min_length=2, max_length=15):
        """
        :param tiles: A list of single-characters representing the player's tiles.
        :param starting_branch: The starting branch in the dictionary tree which we'll be exploring
        :param fixed_tiles: A list of tuples containing a character and the zero-indexed position in the created word
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

        assert (len(fixed_tiles) == 1 or
                all([fixed_tiles[i][1] < fixed_tiles[i + 1][1] for i in range(len(fixed_tiles) - 1)]))

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

        """
        If the word at our current branch is valid, then we'll return it as a possible valid word, but only if there
        aren't required tiles upcoming which would directly attach to this word. For example, if we had the word at our
        current branch 'PIE' with fixed tile ('S', 3), we wouldn't have PIE be a valid word as the word which would
        actually be formed on the board is PIES, and it's much easier to check for that case now rather than appending
        trailing tiles to the board once it has been played.
        """
        if starting_branch['VALID'] and len(starting_branch['WORD']) >= min_length and len(tiles) < len(self.tiles):
            if not fixed_tiles or fixed_tiles[0][1] > len(starting_branch['WORD']):
                valid_words = [starting_branch['WORD']]
            else:
                valid_words = []
        else:
            valid_words = []

        # If our current position features a mandated tile, then we check to see if that's a valid entry at this point
        # in the tree
        if fixed_tiles and fixed_tiles[0][1] == pos:
            if fixed_tiles[0][0] in starting_branch:
                valid_words += self.find_words(tiles=tiles,
                                               starting_branch=starting_branch[fixed_tiles[0][0]],
                                               fixed_tiles=fixed_tiles[1:],
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
                                                       fixed_tiles=fixed_tiles)
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
                                                                 fixed_tiles=fixed_tiles)
                    words_with_blanks = [word[:pos] + word[pos].lower() + word[pos + 1:] for word in words_with_blanks]
                    valid_words += words_with_blanks
        return valid_words

    def get_move_params(self, coords, direction, board_state):
        """
        Asserts that the number of tiles can be placed in the direction dir with the coordinates coords.
        Returns the (zero indexed) number of tiles until this becomes valid, and the ultimate length of the move.
        For example, if we're trying to place seven tiles across line '_ _ A _ _ _ _ _ _ _ _ _ _ _ _ ' from the first
        position, the result would be (2, 8, [(2, A)] as it becomes valid at tile 2 and the maximum number of
        letters in the result will be six.
        :param coords: y and x integer coordinates in tuple
        :param direction: string direction 'D' or 'R' for down or right.
        :param board_state: The list of strings currently representing the tiles played on the board.
        :return a tuple containing the minimum word length and the locations in the word of
        pre-placed tiles.
        :rtype tuple (int, list)
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
        tiles_rem = len(self.tiles)

        tiles_to_validity = -1

        if direction == 'D':
            """
            If the direction is down, then we first check that there is no tile played directly above us, as if that is
            the case then we'd be far better to calculate from that point rather than to allow a move to be formulated
            here and only later check if it aligns with the leading tile.
            """
            if y > 0 and board_state[y-1][x] != ' ':
                return -1, []

            while y < 15 and (tiles_rem or board_state[y][x] != ' '):
                if tiles_to_validity == -1:
                    if not is_island(y, x):
                        tiles_to_validity = y - start_y + 1
                if board_state[y][x] == ' ':
                    tiles_rem -= 1
                else:
                    fixed_tiles.append((board_state[y][x], y - start_y))
                y += 1
            return tiles_to_validity, fixed_tiles
        else:
            """
            Similarly, if going right we first check there's no tile to our immediate left. 
            """
            if x > 0 and board_state[y][x-1] != ' ':
                return -1, []
            while x < 15 and (tiles_rem or board_state[y][x] != ' '):
                if tiles_to_validity == -1:
                    if not is_island(y, x):
                        tiles_to_validity = x - start_x + 1
                if board_state[y][x] == ' ':
                    tiles_rem -= 1
                else:
                    fixed_tiles.append((board_state[y][x], x - start_x))
                x += 1
            return tiles_to_validity, fixed_tiles

    def get_valid_locations(self, board_state):
        """
        :return: A list of "MoveParam" named tuples, containing the coordinates, orientation, min word length
        and max word length for perspective moves.
        """

        MoveParam = namedtuple('MoveParam', 'coords dir min max fixed')

        valid_move_params = []

        for y in range(15):
            for x in range(15):
                for direction in ['D', 'R']:
                    min_len, fixed_tiles = self.get_move_params((y, x), direction, board_state)
                    if min_len != -1:
                        if direction == 'D':
                            valid_move_params.append(MoveParam((y, x), direction, min_len, 15-y, fixed_tiles))
                        else:
                            valid_move_params.append(MoveParam((y, x), direction, min_len, 15-x, fixed_tiles))

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
            valid_words = self.find_words(fixed_tiles=vl.fixed, min_length=max(2, vl.min), max_length=vl.max)
            valid_moves += [Move(vl.coords, vl.dir, word) for word in valid_words]

        # Now we score our prospective moves, and remove the invalid ones.
        move_scores = [(move, self.rulebook.score_move(move, board_state)) for move in valid_moves
                       if self.rulebook.score_move(move, board_state) > 0]

        move_scores = sorted(move_scores, key=lambda x: x[1], reverse=True)

        if move_scores:
            move = move_scores[0][0]
        else:
            # If no moves are available, we send the skip signal which is coordinates of -1, -1
            move = Move((-1, -1), '', '')

        return move
