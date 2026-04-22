"""Row/column/word-path highlighting used while a human types a move."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Highlight:
    """Column / row / word-path to emphasise while the player types."""

    col: int | None = None
    row: int | None = None
    direction: str = ""  # "R" or "D" once the player has typed a direction
    path: tuple[tuple[int, int, str], ...] = field(default_factory=tuple)


def parse_input_highlight(buf: str) -> Highlight:
    """Derive column / row / word-path highlights from an in-progress input buffer."""
    stripped = buf.lstrip().lower()
    if stripped.startswith(("define", "exchange", "skip", "quit", "help")):
        return Highlight()

    tokens = buf.split()
    trailing = bool(buf) and buf[-1].isspace()
    if not tokens:
        return Highlight()

    def coord(tok: str) -> int | None:
        try:
            v = int(tok, 16)
        except ValueError:
            return None
        return v if 0 <= v <= 14 else None

    col = coord(tokens[0])
    if col is None:
        return Highlight()
    if len(tokens) == 1 and not trailing:
        return Highlight(col=col)

    row = coord(tokens[1]) if len(tokens) >= 2 else None
    if row is None:
        return Highlight(col=col)
    if len(tokens) == 2 and not trailing:
        return Highlight(col=col, row=row)

    direction = tokens[2][0].upper() if len(tokens) >= 3 and tokens[2] else ""
    if direction not in ("R", "D"):
        return Highlight(col=col, row=row)

    word = tokens[3] if len(tokens) >= 4 else ""
    path = tuple(
        (row + k if direction == "D" else row,
         col + k if direction == "R" else col,
         ch.upper())
        for k, ch in enumerate(word)
        if ch.isalpha()
        and 0 <= (row + k if direction == "D" else row) < 15
        and 0 <= (col + k if direction == "R" else col) < 15
    )
    return Highlight(col=col, row=row, direction=direction, path=path)
