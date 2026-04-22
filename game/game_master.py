"""Run a match: board, bag, turns, scoring."""

from __future__ import annotations

from random import shuffle

from .board import Board
from .exceptions import QuitGame
from .players import ComputerPlayer, HumanPlayer
from .rulebook import Rulebook
from .tile_bag import TileBag
from .ui import GamePresenter, info, show_launch_splash, success, warn


class GameMaster:
    """Turn loop and scoring until someone goes out or everyone passes."""

    def __init__(self, human_count: int = 0, computer_count: int = 0) -> None:
        """New game master; reset_game runs when play_game starts."""
        self.rulebook = Rulebook()
        self.board: Board | None = None
        self.bag: TileBag | None = None
        self.players: list[HumanPlayer | ComputerPlayer] = []
        self.player_scores: list[int] = []
        self.human_count = human_count
        self.computer_count = computer_count
        self.presenter = GamePresenter()

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
        self.presenter.reset()

    def play_game(self, verbose: bool = False) -> None:
        """Play until passes or a player goes out, then apply endgame adjustments."""
        show_launch_splash()
        self.reset_game()

        consecutive_skips = 0

        shuffle(self.players)
        if verbose:
            self.presenter.announce_turn_order(self.players)

        id_of_first_empty: int | None = None

        assert self.board is not None and self.bag is not None

        turn_number = 0

        while consecutive_skips < len(self.players) and min(len(player.tiles) for player in self.players) > 0:
            for i, player in enumerate(self.players):
                turn_number += 1
                is_human = isinstance(player, HumanPlayer)
                if is_human:
                    self.presenter.print_turn_header(turn_number, player.name, is_human)
                    self.presenter.print_sidebar(self.players, self.player_scores)

                try:
                    move = player.prompt_move(self.board.state, board=self.board)
                except QuitGame:
                    if verbose:
                        warn(f"[bold]{player.name}[/] ends the game.")
                    raise

                if move.coords == (-1, -1):
                    consecutive_skips += 1
                    if verbose:
                        self.presenter.announce_pass(player.name)
                elif move.coords == (-2, -2):
                    self.presenter.announce_exchange(player.name, len(move.word))
                    player.receive_tiles(self.bag.grab(len(move.word)))
                else:
                    consecutive_skips = 0

                    gained = self.rulebook.score_move(move, self.board.state)

                    if isinstance(player, ComputerPlayer):
                        self.presenter.animate_computer_move(
                            self.board,
                            self.players,
                            self.player_scores,
                            i,
                            move,
                            gained,
                        )
                    else:
                        self.player_scores[i] += gained
                        self.board.play_move(move)

                    num_new_tiles = 7 - len(player.tiles)
                    player.receive_tiles(self.bag.grab(num_new_tiles))

                    if verbose:
                        self.presenter.announce_move(player.name, move.word, gained)

                    if len(player.tiles) == 0:
                        id_of_first_empty = player.id
                        if verbose:
                            info(f"[bold]{player.name}[/] has used all their tiles.")
                        break

        self._apply_endgame_scoring(id_of_first_empty, verbose)

        if verbose:
            self.presenter.print_final_board(self.board, self.players, self.player_scores)

    def _apply_endgame_scoring(self, id_of_first_empty: int | None, verbose: bool) -> None:
        """Subtract unplayed racks; if someone emptied their rack, credit them opponents' totals."""
        if id_of_first_empty is None:
            for i, player in enumerate(self.players):
                penalty = self.rulebook.calculate_penalty(player.tiles)
                if penalty and verbose:
                    warn(
                        f"[bold]{player.name}[/] loses "
                        f"[bright_red]{penalty}[/] points for remaining tiles: "
                        f"{', '.join(player.tiles)}"
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
            success(
                f"[bold]{self.players[finisher_idx].name}[/] gains "
                f"[bright_green]{others_total}[/] points from opponents' unplayed tiles."
            )

        for i, player in enumerate(self.players):
            if player.id == id_of_first_empty:
                continue
            penalty = self.rulebook.calculate_penalty(player.tiles)
            if verbose and penalty:
                warn(
                    f"[bold]{player.name}[/] loses "
                    f"[bright_red]{penalty}[/] points for remaining tiles: "
                    f"{', '.join(player.tiles)}"
                )
            self.player_scores[i] -= penalty

    def print_score_sheet(self) -> None:
        """Print the current score sheet on the shared console."""
        self.presenter.print_score_sheet(self.players, self.player_scores)
