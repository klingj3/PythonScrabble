import os
import sys
import random


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
        Player.__init__(self, id, init_tiles, name)
        # We build a tree from this dictionary of words.
        # TODO: Time comparison vs brute forcing dictionary set
        dictionary_tree = {'VALID': False, 'WORD': ''}
        with open("docs/dictionary.txt") as dictfile:
            dictionary_lines = [word.replace('\n', '') for word in dictfile]

        for word in dictionary_lines:
            active_branch = dictionary_tree
            for i, character in enumerate(word):
                if character not in active_branch:
                    active_branch[character] = {'VALID': False, 'WORD': active_branch['WORD'] + character}
                active_branch = active_branch[character]
                if i == len(word) - 1:
                    active_branch['VALID'] = True

        self.dictionary = dictionary_tree

    def find_words(self, tiles=None, starting_branch=None):
        """
        :param tiles: A list of single-characters representing the player's tiles.
        :param starting_branch: The starting branch in the dictionary tree which we'll be exploring
        :param valid_words: Correct words made with the tiles
        :return: A list of valid words from the tiles given from the starting branch given
        """
        # One of the quirks of Python, default arguments can't be local variables
        if tiles is None:
            tiles = self.tiles.copy()
        if starting_branch is None:
            starting_branch = self.dictionary

        def without(full_list, item):
            """
            :param full)list: A list of objects
            :param item: Item to be removed
            :return: A copy of the list with the item removed.
            """
            local_list = full_list.copy()
            if item in local_list:
                local_list.remove(item)
            return local_list

        valid_words = [starting_branch['WORD']] if starting_branch['VALID'] else []

        for tile in tiles:
            if tile in starting_branch:
                valid_words += self.find_words(without(tiles, tile), starting_branch=starting_branch[tile])

        # If this is the parent branch, we'll sort before returning from longest to shortest.
        if starting_branch['WORD'] == '':
            valid_words = sorted(valid_words, key=len, reverse=True)
        return valid_words

    def test_word(self, word):
        active_branch = self.dictionary
        for character in word:
            if character not in active_branch:
                return False
            active_branch = active_branch[character]
        return active_branch['VALID']
