"""Rich-based UI: console, colours, panels, highlights, and the game-loop presenter."""

from __future__ import annotations

from .console import console, error, info, success, warn
from .highlight import Highlight, parse_input_highlight
from .panels import goodbye_banner, legend, rack_panel, show_launch_splash
from .presenter import GamePresenter
from .styles import (
    BLANK_TILE_STYLE,
    BONUS_GLYPHS,
    BONUS_STYLES,
    TILE_STYLE,
    bonus_cell,
    tile_cell,
)

__all__ = [
    "BLANK_TILE_STYLE",
    "BONUS_GLYPHS",
    "BONUS_STYLES",
    "GamePresenter",
    "Highlight",
    "TILE_STYLE",
    "bonus_cell",
    "console",
    "error",
    "goodbye_banner",
    "info",
    "legend",
    "parse_input_highlight",
    "rack_panel",
    "show_launch_splash",
    "success",
    "tile_cell",
    "warn",
]
