# Python command-line Scrabble

A terminal Scrabble implementation for local hot-seat play or against computer opponents that search the move space each turn.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Setup

From the repository root:

```bash
uv sync --extra dev
```

Or with pip:

```bash
python3 -m pip install -e ".[dev]"
```

Copy `.env.example` to `.env` if you need to override where data files live (see **Data files** below).

## Data files

Dictionary and tile data are loaded from the directory pointed to by **`DATA_ROOT`**. If unset, it defaults to `game/data` next to the installed package (the usual layout in this repo).

You can set `DATA_ROOT` in a `.env` file at the project root (loaded automatically via `python-dotenv`) or export it in your shell.

## Run the game

```bash
uv run scrabble
uv run scrabble <human_players> <computer_players>
```

Or:

```bash
python3 -m game
python3 game_manager.py
```

### Moves (human)

- `quit` — leave the game
- `skip` — pass the turn
- `exchange <LETTERS>` — trade tiles (when bag rules allow)
- `define <WORD>` — look up a definition (when available)
- `<x> <y> <R|D> <WORD>` — play at column `x`, row `y`, direction right or down (coordinates use the same hex digit column headers as the printed board)

## Development

```bash
uv run pytest
uv run mypy game tests
```

Type checking targets the `game` package and `tests` with strict defaults (`pyproject.toml`).

## Layout

- `game/board.py` — board state and rendering
- `game/rulebook.py` — dictionary, scoring, validation
- `game/tile_bag.py` — tile pool
- `game/game_master.py` — turn loop and scoring
- `game/players/` — human and computer players
- `game/paths.py` — `DATA_ROOT` / `data_path()`
- `tests/` — pytest suite

The evaluation notebook under `jupyter_notebooks/` sets `DATA_ROOT` from the working directory; optional extras such as matplotlib/pandas are not part of the core package.
