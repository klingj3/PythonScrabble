"""CLI entry point."""

from __future__ import annotations

import sys

from .exceptions import QuitGame
from .game_master import GameMaster


def main() -> int:
    """Run from argv; exit 0 even when the player quits."""
    try:
        if len(sys.argv) == 1:
            gm = GameMaster(human_count=1, computer_count=1)
            gm.play_game(True)
        else:
            human_count = int(sys.argv[1])
            computer_count = int(sys.argv[2])
            gm = GameMaster(human_count, computer_count)
            gm.play_game(True)
    except QuitGame:
        pass
    return 0
