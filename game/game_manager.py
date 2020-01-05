from scrabble_box import Board, Rulebook, TileBag
from scrabble_players import HumanPlayer, AIPlayer
from random import shuffle

import sys

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
        self.rulebook = Rulebook()
        self.players = []
        for i in range(ai_count):
            self.players.append(AIPlayer(id=1+human_count+i, init_tiles=self.bag.grab(7), rulebook=self.rulebook, name="AI {}".format(i+1)))
        for i in range(human_count):
            self.players.append(HumanPlayer(id=i+1, init_tiles=self.bag.grab(7), rulebook=self.rulebook))
        self.player_scores = [0 for _ in range(len(self.players))]

    def play_game(self):
        """
        Cycle through the players in the list, prompting them for their individual moves until the game is over.
        :return: None
        """

        # We keep track of the consecutive skips as this is one of the conditions which can lead to the game's end.
        consecutive_skips = 0

        shuffle(self.players)
        print("Player order is: {}".format(', '.join([player.name for player in self.players])))

        id_of_first = None

        # The game ends when oen player has used all of their tiles, or if everyone skips for two turns because nothing
        # can be placed. (This is very unlikely, but must be included as an edge case.
        while consecutive_skips < len(self.players) and min([len(player.tiles) for player in self.players]) > 0:
            for i, player in enumerate(self.players):

                if isinstance(player, HumanPlayer):
                    self.print_score_sheet()
                    print(self.board)

                move = player.prompt_move(self.board.state)

                if move.coords == (-1, -1):
                    consecutive_skips += 1
                elif move.coords == (-2, -2):
                    print("Player exchanges {} tiles.".format(len(move.word)))
                    player.receive_tiles(self.bag.grab(len(move.word)))
                elif move.coords == (-3, -3):
                    print("Player {} ends the game.".format(player.name))
                    exit(0)
                else:
                    consecutive_skips = 0

                    self.player_scores[i] += self.rulebook.score_move(move, self.board.state)

                    # Place this move on the board.
                    self.board.play_move(move)
                    num_new_tiles = 7 - len(player.tiles)
                    player.receive_tiles(self.bag.grab(num_new_tiles))

                    if len(player.tiles) == 0:
                        id_of_first = player.id
                        print("Player {} has used all their tiles".format(player.name))
                        break

        for i, player in enumerate(self.players):
            if player.id != id_of_first:
                penalty = self.rulebook.calculate_penalty(player.tiles)
                print("{} loses {} points for remaining tiles: {}".format(player.name, penalty, ', '.join(player.tiles)))
                self.player_scores[i] -= penalty

        print(self.board)
        self.print_score_sheet()

    def print_score_sheet(self):
        """
        Prints the scores of all players, with the current player being last.
        :return: None
        """
        for i, opponent in enumerate(self.players):
            print("{}: {} pts".format(opponent.name, self.player_scores[i]))
        return None


if __name__ == '__main__':
    if len(sys.argv) == 1:
        gm = GameMaster(human_count=1, ai_count=1)
        gm.play_game()
    else:
        human_count = int(sys.argv[1])
        ai_count = int(sys.argv[2])
        gm = GameMaster(human_count, ai_count)
        gm.play_game()
