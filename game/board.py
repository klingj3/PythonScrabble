"""Scrabble board representation and move application."""

from __future__ import annotations

from colorama import Fore, Style

from .types import BoardState, Move


class Board:
    """15×15 grid with premium-square layout and applied letters."""

    def __init__(self) -> None:
        """Initialize empty rows and the standard premium-square pattern."""
        self.special_tiles: list[str] = [
            "W  l   W   l  W",
            " w   L   L   w ",
            "  w   l l   w  ",
            "l  w   l   w  l",
            "    w     w    ",
            " L   L   L   L ",
            "  l   l l   l  ",
            "W  l   *   l  W",
            "  l   l l   l  ",
            " L   L   L   L ",
            "    w     w    ",
            "l  w   l   w  l",
            "  w   l l   w  ",
            " w   L   L   w ",
            "W  l   W   l  W",
        ]
        self.state: BoardState = ["".join([" " for _ in range(15)]) for _ in range(15)]

    def __str__(self) -> str:
        """Return a colorized ASCII view with hex row/column indices."""
        reset = Style.RESET_ALL
        special_tile_color = {
            " ": "",
            "W": Fore.RED,
            "w": Fore.MAGENTA,
            "L": Fore.BLUE,
            "l": Fore.CYAN,
            "*": Fore.MAGENTA,
        }

        string_rep = "   " + " ".join([str(hex(x))[-1] for x in range(15)]) + "\n"
        for i in range(15):
            line = ""
            for j, tile in enumerate(self.state[i]):
                if tile != " ":
                    line += tile
                else:
                    line += special_tile_color[self.special_tiles[i][j]] + self.special_tiles[i][j] + reset
                line += " "
            string_rep += str(hex(i))[-1] + "  " + line + reset + "\n"
        return string_rep + reset

    def play_move(self, move: Move) -> bool:
        """Place ``move.word`` on ``state`` at ``move.coords`` in ``move.dir``."""
        y, x = move.coords
        if move.dir == "D":
            for i, c in enumerate(move.word):
                row = self.state[y + i]
                self.state[y + i] = row[:x] + c + row[x + 1 :]
        if move.dir == "R":
            row = self.state[y]
            self.state[y] = row[:x] + move.word + row[x + len(move.word) :]
        return True
