from game.scrabble_box import Board, Rulebook, TileBag
from game.scrabble_players import HumanPlayer, AIPlayer


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
        for i in range(human_count):
            self.players.append(HumanPlayer(id=i, init_tiles=self.bag.grab(7)))
        for i in range(ai_count):
            self.players.append(AIPlayer(id=human_count+i, init_tiles=self.bag.grab(7), name="AI {}".format(i+1)))
        self.player_scores = [0 for _ in range(len(self.players))]

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
        while consecutive_skips < 2*player_count and min([len(player.tiles) for player in self.players]) > 0:
            for i, player in enumerate(self.players):

                if isinstance(player, HumanPlayer):
                    print(self.board)
                    for j, opponent in enumerate(self.players):
                        if j != i:
                            print("{}: {} pts".format(opponent.name, self.player_scores[i]))
                    print("{}: {} pts -- {}".format(player.name, self.player_scores[i], player.tiles))

                move = player.prompt_move(self.board.state)

                if move.coords == (-1, -1):
                    consecutive_skips += 1
                else:
                    consecutive_skips = 0

                    self.player_scores[i] += self.rulebook.score_move(move, self.board.state)

                    # Place this move on the board.
                    self.board.play_move(move)
                    num_new_tiles = 7 - len(player.tiles)
                    player.receive_tiles(self.bag.grab(num_new_tiles))

                    if len(player.tiles) == 0:
                        break

        print(self.board)
        for i, player in enumerate(self.players):
            print("{}: {} pts".format(player.name, self.player_scores[i]))


if __name__ == '__main__':
    gm = GameMaster(human_count=1, ai_count=1)
    gm.play_game()