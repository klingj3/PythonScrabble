"""Scrabble board representation and move application."""

from __future__ import annotations

from dataclasses import dataclass, field

from rich.console import Console, ConsoleOptions, RenderResult
from rich.text import Text

from .types import BoardState, Move
from .ui import BLANK_TILE_STYLE, PREMIUM_GLYPHS, PREMIUM_STYLES, TILE_STYLE


@dataclass
class Highlight:
    """Column / row / word-path to emphasise while the player types."""

    col: int | None = None
    row: int | None = None
    path: tuple[tuple[int, int, str], ...] = field(default_factory=tuple)


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
        self.highlight: Highlight | None = None

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        """Yield Rich Text lines forming the coloured board grid."""
        hl = self.highlight or Highlight()
        path_chars: dict[tuple[int, int], str] = {
            (r, c): ch for r, c, ch in hl.path
        }

        # Column header
        header = Text("    ")
        for c in range(15):
            col_hex = format(c, "x")
            if hl.col == c and hl.row is None:
                header.append(f" {col_hex} ", style="bold bright_yellow underline")
            else:
                header.append(f" {col_hex} ", style="grey50")
        yield header

        for r in range(15):
            row_hex = format(r, "x")
            line = Text()
            if hl.row == r and hl.col is None:
                line.append(f"{row_hex}  ", style="bold bright_yellow underline")
            else:
                line.append(f"{row_hex}  ", style="grey50")

            for c in range(15):
                tile = self.state[r][c]
                if (r, c) in path_chars:
                    ch = path_chars[(r, c)]
                    line.append(f" {ch.upper()} ", style="bold black on bright_green")
                elif tile != " ":
                    style = BLANK_TILE_STYLE if tile.islower() else TILE_STYLE
                    line.append(f" {tile.upper()} ", style=style)
                else:
                    marker = self.special_tiles[r][c]
                    if hl.col == c and hl.row == r:
                        glyph = PREMIUM_GLYPHS.get(marker, "·")
                        line.append(f" {glyph} ", style="bold black on bright_green")
                    elif hl.col == c and hl.row is None:
                        glyph = PREMIUM_GLYPHS.get(marker, "·")
                        line.append(f" {glyph} ", style="bold bright_yellow")
                    elif hl.row == r and hl.col is None:
                        glyph = PREMIUM_GLYPHS.get(marker, "·")
                        line.append(f" {glyph} ", style="bold bright_yellow")
                    else:
                        glyph = PREMIUM_GLYPHS.get(marker, "·")
                        style = PREMIUM_STYLES.get(marker, "grey50")
                        line.append(f" {glyph} ", style=style)
            yield line

    def play_move(self, move: Move) -> bool:
        """Write the word into the grid at coords along move.dir."""
        y, x = move.coords
        if move.dir == "D":
            for i, c in enumerate(move.word):
                row = self.state[y + i]
                self.state[y + i] = row[:x] + c + row[x + 1 :]
        if move.dir == "R":
            row = self.state[y]
            self.state[y] = row[:x] + move.word + row[x + len(move.word) :]
        return True
