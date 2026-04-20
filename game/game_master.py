"""Orchestrates board, bag, players, and scoring."""

from __future__ import annotations

from random import shuffle

from .board import Board
from .exceptions import QuitGame
from .players import ComputerPlayer, HumanPlayer
from .rulebook import Rulebook
from .tile_bag import TileBag


class GameMaster:
    """Runs turns, applies moves, and updates scores until the game ends."""

    def __init__(self, human_count: int = 0, computer_count: int = 0) -> None:
        """Create a game master (``reset_game`` runs at the start of ``play_game``)."""
        self.rulebook = Rulebook()
        self.board: Board | None = None
        self.bag: TileBag | None = None
        self.players: list[HumanPlayer | ComputerPlayer] = []
        self.player_scores: list[int] = []
        self.human_count = human_count
        self.computer_count = computer_count

    def reset_game(self) -> None:
        """Build a fresh board, bag, player list, and zeroed scores."""
        self.board = Board()
        self.bag = TileBag()
        self.players = []
        for i in range(self.computer_count):
            self.players.append(
                ComputerPlayer(
                    player_id=1 + self.human_count + i,
                    init_tiles=self.bag.grab(7),
                    rulebook=self.rulebook,
                    name="Computer {}".format(i + 1),
                )
            )
        for i in range(self.human_count):
            self.players.append(
                HumanPlayer(
                    player_id=i + 1,
                    init_tiles=self.bag.grab(7),
                    rulebook=self.rulebook,
                )
            )
        self.player_scores = [0 for _ in range(len(self.players))]

    def play_game(self, verbose: bool = False) -> None:
        """Play until passes or a player goes out, then apply endgame adjustments."""
        self.reset_game()

        consecutive_skips = 0

        shuffle(self.players)
        if verbose:
            print("Player order is: {}".format(", ".join([player.name for player in self.players])))

        id_of_first_empty: int | None = None

        assert self.board is not None and self.bag is not None

        while consecutive_skips < len(self.players) and min(len(player.tiles) for player in self.players) > 0:
            for i, player in enumerate(self.players):
                if isinstance(player, HumanPlayer):
                    self.print_score_sheet()
                    print(self.board)

                try:
                    move = player.prompt_move(self.board.state)
                except QuitGame:
                    if verbose:
                        print("Player {} ends the game.".format(player.name))
                    raise

                if move.coords == (-1, -1):
                    consecutive_skips += 1
                elif move.coords == (-2, -2):
                    print("Player exchanges {} tiles.".format(len(move.word)))
                    player.receive_tiles(self.bag.grab(len(move.word)))
                else:
                    consecutive_skips = 0

                    self.player_scores[i] += self.rulebook.score_move(move, self.board.state)

                    self.board.play_move(move)
                    num_new_tiles = 7 - len(player.tiles)
                    player.receive_tiles(self.bag.grab(num_new_tiles))

                    if len(player.tiles) == 0:
                        id_of_first_empty = player.id
                        if verbose:
                            print("Player {} has used all their tiles".format(player.name))
                        break

        self._apply_endgame_scoring(id_of_first_empty, verbose)

        if verbose:
            print(self.board)
            self.print_score_sheet()

    def _apply_endgame_scoring(self, id_of_first_empty: int | None, verbose: bool) -> None:
        """Subtract unplayed racks; if someone emptied their rack, credit them opponents' totals."""
        if id_of_first_empty is None:
            for i, player in enumerate(self.players):
                penalty = self.rulebook.calculate_penalty(player.tiles)
                if penalty and verbose:
                    print(
                        "{} loses {} points for remaining tiles: {}".format(
                            player.name, penalty, ", ".join(player.tiles)
                        )
                    )
                self.player_scores[i] -= penalty
            return

        finisher_idx = next(i for i, p in enumerate(self.players) if p.id == id_of_first_empty)
        others_total = sum(
            self.rulebook.calculate_penalty(p.tiles)
            for j, p in enumerate(self.players)
            if j != finisher_idx
        )
        self.player_scores[finisher_idx] += others_total
        if verbose and others_total:
            print(
                "{} gains {} points from opponents' unplayed tiles.".format(
                    self.players[finisher_idx].name, others_total
                )
            )

        for i, player in enumerate(self.players):
            if player.id == id_of_first_empty:
                continue
            penalty = self.rulebook.calculate_penalty(player.tiles)
            if verbose and penalty:
                print(
                    "{} loses {} points for remaining tiles: {}".format(
                        player.name, penalty, ", ".join(player.tiles)
                    )
                )
            self.player_scores[i] -= penalty

    def print_score_sheet(self) -> None:
        """Print each player's running total on stdout."""
        for i, opponent in enumerate(self.players):
            print("{}: {} pts".format(opponent.name, self.player_scores[i]))
