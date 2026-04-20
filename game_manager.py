"""Backward-compatible launcher; prefer `uv run scrabble` or `python -m game`."""

from game.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
