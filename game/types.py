"""Shared types for moves and board rows (``BoardState``, ``Direction``)."""

from __future__ import annotations

from typing import Literal, NamedTuple


class Move(NamedTuple):
    """Played or meta-move: ``coords`` (row, col), direction, and word or exchanged letters."""

    coords: tuple[int, int]
    dir: str
    word: str


BoardState = list[str]  #: Fifteen strings of fifteen characters (rows).
Direction = Literal["R", "D"]  #: Primary word axis for a play.
