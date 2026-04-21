"""Run a match: board, bag, turns, scoring."""

from __future__ import annotations

import time
from random import shuffle

from rich.columns import Columns
from rich.console import Group, RenderableType
from rich.live import Live
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from .board import Board, Highlight
from .exceptions import QuitGame
from .players import ComputerPlayer, HumanPlayer
from .rulebook import Rulebook
from .tile_bag import TileBag
from .types import Move
from .ui import console, info, legend, success, warn


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
        self.last_message: RenderableType | None = None

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
        self.last_message = None

        consecutive_skips = 0

        shuffle(self.players)
        if verbose:
            order = Text(" → ", style="grey50").join(
                Text(p.name, style="bold bright_white") for p in self.players
            )
            self.last_message = Panel(
                order, title="Turn order", border_style="cyan", padding=(0, 1)
            )

        id_of_first_empty: int | None = None

        assert self.board is not None and self.bag is not None

        turn_number = 0

        while consecutive_skips < len(self.players) and min(len(player.tiles) for player in self.players) > 0:
            for i, player in enumerate(self.players):
                turn_number += 1
                console.clear()
                if isinstance(player, HumanPlayer):
                    console.print(Rule(f"[bold bright_magenta]Turn {turn_number} — {player.name}[/]", style="bright_magenta"))
                    console.print(self._sidebar())
                else:
                    console.print(Rule(f"[dim]Turn {turn_number} — {player.name}[/]", style="grey50"))

                try:
                    move = player.prompt_move(self.board.state, board=self.board)
                except QuitGame:
                    if verbose:
                        warn(f"[bold]{player.name}[/] ends the game.")
                    raise

                if move.coords == (-1, -1):
                    consecutive_skips += 1
                    if verbose:
                        self.last_message = self._last_move_panel(
                            f"[bold]{player.name}[/] passes their turn."
                        )
                elif move.coords == (-2, -2):
                    self.last_message = self._last_move_panel(
                        f"[bold]{player.name}[/] exchanges {len(move.word)} tile(s)."
                    )
                    player.receive_tiles(self.bag.grab(len(move.word)))
                else:
                    consecutive_skips = 0

                    gained = self.rulebook.score_move(move, self.board.state)

                    if isinstance(player, ComputerPlayer):
                        self._animate_computer_move(i, move, gained)
                    else:
                        self.player_scores[i] += gained
                        self.board.play_move(move)

                    num_new_tiles = 7 - len(player.tiles)
                    player.receive_tiles(self.bag.grab(num_new_tiles))

                    if verbose:
                        self.last_message = self._last_move_panel(
                            f"[bold]{player.name}[/] plays "
                            f"[bold bright_yellow]{move.word.upper()}[/] for "
                            f"[bold bright_green]{gained}[/] pts."
                        )

                    if len(player.tiles) == 0:
                        id_of_first_empty = player.id
                        if verbose:
                            info(f"[bold]{player.name}[/] has used all their tiles.")
                        break

        self._apply_endgame_scoring(id_of_first_empty, verbose)

        if verbose:
            console.print(Rule("[bold bright_magenta]Final board[/]", style="bright_magenta"))
            console.print(self.board)
            console.print(self._score_sheet(final=True))

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

    def _last_move_panel(self, markup: str) -> Panel:
        """Panel shown in the sidebar describing the prior player's action."""
        return Panel(Text.from_markup(markup), title="Last move",
                     border_style="cyan", padding=(0, 1))

    def _sidebar(
        self,
        scores: list[int] | None = None,
        highlight_index: int | None = None,
    ) -> RenderableType:
        """Scoreboard + legend + (optional) last-move panel, laid out horizontally."""
        bits: list[RenderableType] = [
            self._score_sheet(scores=scores, highlight_index=highlight_index),
            legend(),
        ]
        if self.last_message is not None:
            bits.append(self.last_message)
        return Columns(bits, expand=False, padding=(0, 2))

    def _score_sheet(
        self,
        final: bool = False,
        scores: list[int] | None = None,
        highlight_index: int | None = None,
    ) -> Panel:
        """Score table; optional alternate scores and highlighted row (e.g. during animations)."""
        shown = scores if scores is not None else self.player_scores
        ranked = sorted(
            enumerate(self.players),
            key=lambda item: shown[item[0]],
            reverse=True,
        )

        table = Table.grid(padding=(0, 2))
        table.add_column(justify="right", style="bold grey70")
        table.add_column(style="bold bright_white")
        table.add_column(justify="right", style="bold bright_green")

        for rank, (i, player) in enumerate(ranked, start=1):
            marker = "★" if final and rank == 1 else str(rank)
            if final and rank == 1:
                score_style = "bold bright_yellow"
            elif i == highlight_index:
                score_style = "bold reverse bright_yellow"
            else:
                score_style = "bold bright_green"
            table.add_row(
                marker,
                player.name,
                Text(f"{shown[i]} pts", style=score_style),
            )

        title = "[bold bright_yellow]Final Scores[/]" if final else "[bold bright_cyan]Scoreboard[/]"
        return Panel(table, title=title, border_style="bright_yellow" if final else "cyan", padding=(0, 1))

    def print_score_sheet(self) -> None:
        """Print the current score sheet on the shared console."""
        console.print(self._score_sheet())

    def _animate_computer_move(
        self,
        player_idx: int,
        move: Move,
        gained: int,
        tile_delay: float = 0.14,
        score_duration: float = 0.55,
        hold_after: float = 0.35,
    ) -> None:
        """Animate tiles landing, then tick the score up; board state ends fully updated."""
        assert self.board is not None
        board = self.board

        before = self.player_scores[player_idx]
        after = before + gained

        y, x = move.coords
        is_d = move.dir == "D"
        board.highlight = Highlight(
            row=y if not is_d else None,
            col=x if is_d else None,
        )

        def frame(scores: list[int], highlight_idx: int | None) -> RenderableType:
            return Group(
                self._sidebar(scores=scores, highlight_index=highlight_idx),
                board,
            )

        running_scores = list(self.player_scores)

        try:
            with Live(
                frame(running_scores, None),
                console=console,
                auto_refresh=False,
                transient=False,
            ) as live:
                time.sleep(0.2)

                new_positions = 0
                for i, c in enumerate(move.word):
                    cy, cx = (y + i, x) if is_d else (y, x + i)
                    if board.state[cy][cx] == " ":
                        row = board.state[cy]
                        board.state[cy] = row[:cx] + c + row[cx + 1 :]
                        new_positions += 1
                        live.update(frame(running_scores, None), refresh=True)
                        time.sleep(tile_delay)

                if gained != 0:
                    steps = max(8, min(abs(gained), 20))
                    step_delay = score_duration / steps
                    for s in range(1, steps + 1):
                        running_scores[player_idx] = before + round(gained * s / steps)
                        live.update(frame(running_scores, player_idx), refresh=True)
                        time.sleep(step_delay)

                running_scores[player_idx] = after
                live.update(frame(running_scores, player_idx), refresh=True)
                time.sleep(hold_after)
                live.update(frame(running_scores, None), refresh=True)
        finally:
            board.highlight = None

        self.player_scores[player_idx] = after
