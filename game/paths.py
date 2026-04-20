"""Resolve game data directories via DATA_ROOT or package defaults."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def get_data_root() -> Path:
    """Return the directory holding ``tile_scores.json``, dictionaries, etc."""
    raw = os.environ.get("DATA_ROOT")
    if raw:
        return Path(raw).expanduser().resolve()
    return Path(__file__).resolve().parent / "data"


def data_path(*parts: str) -> Path:
    """Return ``get_data_root()`` with additional path segments joined."""
    return get_data_root().joinpath(*parts)
