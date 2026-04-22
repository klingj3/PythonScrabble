"""Move and board row types."""

from __future__ import annotations

from typing import Literal, NamedTuple


class Move(NamedTuple):
    """One play, pass, or exchange: row/col, axis (R/D), letters."""

    coords: tuple[int, int]
    dir: str
    word: str


BoardState = list[str]  # Fifteen strings of fifteen characters (rows).
Direction = Literal["R", "D"]
