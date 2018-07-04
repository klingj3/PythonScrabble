from collections import namedtuple

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

    def prompt_move(self, board_state):
        """
        :param board_state: The current board
        :return: A string representing the player's desired move, or a reordering of the tiles.
        """
        pass

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
    def __init__(self, id, init_tiles, name=None):
        Player.__init__(self, id, init_tiles, name="AI {}".format(id))

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
        """
        self.dictionary_root, self.dictionary_set = self.generate_dictionary_tree()

    def find_words(self, tiles=None, starting_branch=None, req_tiles=[], pos=0, max_length=15):
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

        # One of the quirks of Python, default arguments can't be local variables
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

        valid_words = [starting_branch['WORD']] if starting_branch['VALID'] else []

        # If our current position features a mandated tile, then we check to see if that's a valid entry at this point
        # in the tree
        if req_tiles and req_tiles[0][1] == pos:
            if req_tiles[0][0] in starting_branch:
                valid_words += self.find_words(tiles, starting_branch[req_tiles[0][0]], req_tiles[1:], pos=pos+1)
        else:
            for tile in tiles:
                if tile in starting_branch:
                    valid_words += self.find_words(without(tiles, tile), starting_branch[tile], pos=pos+1)
        return valid_words

    def generate_dictionary_tree(self):
        """
        :return: The tree-like dictionary showing the relationships between words, used in the faster traversal and
        generating of anagram solutions than just changing all combinations against a set of dictionary words.
        """
        # Normally we'll generate this tree by loading the JSON, but this method is good to include so that this
        # tree can be remade for differing dictionaries as well as incase some error is found in the current
        # dictionar-tree down the line.

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

    def prompt_move(self, board_state):

        Move = namedtuple('Move', 'coords dir length')

        def get_valid_locations(max_num_tiles=7):
            """
            :param max_num_tiles: The longest number of tiles to be used in this position.
            :return: A list of "Move" named tuples.
            """

            def is_island(y, x):
                """
                :param y: Integer Y coordinate
                :param x: Integer X coordinate
                :return:
                """
                if board_state[y][x] == '*':
                    return True

                min_x, max_x = max(x-1, 0), min(x+1, len(board_state[0]))
                min_y, max_y = max(y-1, 0), min(y+1, len(board_state))
                for y in range(min_y, max_y+1):
                    for x in range(min_x, max_x+1):
                        if board_state[y][x] != ' ' and board_state[y][x] != '*':
                            return True
                return False

            valid_moves = []

            # Check moves for the down direction

            # Check moves for the right direction




    def test_word(self, word):
        """
        Tests if a word exists in the scrabble dictionary or not
        :param word: A string of capital letters to be tested
        :return: True if the word is in the dictionary, false otherwise
        """
        return word in self.dictionary_set
