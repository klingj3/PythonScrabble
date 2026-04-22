"""Game-loop presentation: turn headers, scoreboard, animations, announcements."""

from __future__ import annotations

import time
from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol

from rich.columns import Columns
from rich.console import Group, RenderableType
from rich.live import Live
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from .console import console
from .highlight import Highlight
from .panels import legend

if TYPE_CHECKING:
    from ..board import Board
    from ..types import Move


class _NamedPlayer(Protocol):
    """Minimal surface the presenter needs from a player object."""

    name: str


class GamePresenter:
    """Owns loop-scoped display state and renders everything the game shows."""

    def __init__(self) -> None:
        """Start with no prior-move message."""
        self.last_message: RenderableType | None = None

    def reset(self) -> None:
        """Drop any carried-over announcement from a previous game."""
        self.last_message = None

    def announce_turn_order(self, players: Sequence[_NamedPlayer]) -> None:
        """Stash the shuffled turn order so it shows on the first human turn."""
        order = Text(" → ", style="grey50").join(
            Text(p.name, style="bold bright_white") for p in players
        )
        self.last_message = Panel(
            order, title="Turn order", border_style="cyan", padding=(0, 1)
        )

    def announce_pass(self, player_name: str) -> None:
        """Record a pass message for the next sidebar render."""
        self.last_message = self._last_move_panel(
            f"[bold]{player_name}[/] passes their turn."
        )

    def announce_exchange(self, player_name: str, tile_count: int) -> None:
        """Record an exchange message for the next sidebar render."""
        self.last_message = self._last_move_panel(
            f"[bold]{player_name}[/] exchanges {tile_count} tile(s)."
        )

    def announce_move(self, player_name: str, word: str, gained: int) -> None:
        """Record a scored-move message for the next sidebar render."""
        self.last_message = self._last_move_panel(
            f"[bold]{player_name}[/] plays "
            f"[bold bright_yellow]{word.upper()}[/] for "
            f"[bold bright_green]{gained}[/] pts."
        )

    def print_turn_header(self, turn_number: int, player_name: str, is_human: bool) -> None:
        """Clear the screen and draw the turn rule for the current player."""
        console.clear()
        if is_human:
            console.print(Rule(
                f"[bold bright_magenta]Turn {turn_number} — {player_name}[/]",
                style="bright_magenta",
            ))
        else:
            console.print(Rule(
                f"[dim]Turn {turn_number} — {player_name}[/]",
                style="grey50",
            ))

    def print_sidebar(
        self,
        players: Sequence[_NamedPlayer],
        scores: Sequence[int],
    ) -> None:
        """Print the sidebar (scoreboard + legend + last move) on the console."""
        console.print(self._sidebar(players, scores))

    def print_score_sheet(
        self,
        players: Sequence[_NamedPlayer],
        scores: Sequence[int],
        final: bool = False,
    ) -> None:
        """Print just the scoreboard; used for standalone inspection or the finale."""
        console.print(self._score_sheet(players, scores, final=final))

    def print_final_board(self, board: Board, players: Sequence[_NamedPlayer], scores: Sequence[int]) -> None:
        """Print the end-of-game rule, board, and final scores."""
        console.print(Rule("[bold bright_magenta]Final board[/]", style="bright_magenta"))
        console.print(board)
        console.print(self._score_sheet(players, scores, final=True))

    def animate_computer_move(
        self,
        board: Board,
        players: Sequence[_NamedPlayer],
        scores: list[int],
        player_idx: int,
        move: Move,
        gained: int,
        tile_delay: float = 0.14,
        score_duration: float = 0.55,
        hold_after: float = 0.35,
    ) -> None:
        """Animate tiles landing and a score tick; mutates board.state and scores in place."""
        before = scores[player_idx]
        after = before + gained

        y, x = move.coords
        is_d = move.dir == "D"
        board.highlight = Highlight(
            row=y if not is_d else None,
            col=x if is_d else None,
        )

        def frame(running_scores: Sequence[int], highlight_idx: int | None) -> RenderableType:
            return Group(
                self._sidebar(players, running_scores, highlight_index=highlight_idx),
                board,
            )

        running_scores = list(scores)

        console.clear()
        try:
            with Live(
                frame(running_scores, None),
                console=console,
                auto_refresh=False,
                transient=False,
            ) as live:
                time.sleep(0.2)

                for i, c in enumerate(move.word):
                    cy, cx = (y + i, x) if is_d else (y, x + i)
                    if board.state[cy][cx] == " ":
                        row = board.state[cy]
                        board.state[cy] = row[:cx] + c + row[cx + 1 :]
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

        scores[player_idx] = after

    def _last_move_panel(self, markup: str) -> Panel:
        """Panel describing the prior player's action, shown in the sidebar."""
        return Panel(
            Text.from_markup(markup),
            title="Last move",
            border_style="cyan",
            padding=(0, 1),
        )

    def _sidebar(
        self,
        players: Sequence[_NamedPlayer],
        scores: Sequence[int],
        highlight_index: int | None = None,
    ) -> RenderableType:
        """Scoreboard + legend + (optional) last-move panel, laid out horizontally."""
        bits: list[RenderableType] = [
            self._score_sheet(players, scores, highlight_index=highlight_index),
            legend(),
        ]
        if self.last_message is not None:
            bits.append(self.last_message)
        return Columns(bits, expand=False, padding=(0, 2))

    def _score_sheet(
        self,
        players: Sequence[_NamedPlayer],
        scores: Sequence[int],
        final: bool = False,
        highlight_index: int | None = None,
    ) -> Panel:
        """Score table; optional highlighted row (used during score-tick animations)."""
        ranked = sorted(
            enumerate(players),
            key=lambda item: scores[item[0]],
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
                Text(f"{scores[i]} pts", style=score_style),
            )

        title = "[bold bright_yellow]Final Scores[/]" if final else "[bold bright_cyan]Scoreboard[/]"
        return Panel(
            table,
            title=title,
            border_style="bright_yellow" if final else "cyan",
            padding=(0, 1),
        )
