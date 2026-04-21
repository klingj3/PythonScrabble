"""Resolve game data directories via DATA_ROOT or package defaults."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def get_data_root() -> Path:
    """Directory with tile_scores.json, dictionaries, and other data files."""
    raw = os.environ.get("DATA_ROOT")
    if raw:
        return Path(raw).expanduser().resolve()
    return Path(__file__).resolve().parent / "data"


def data_path(*parts: str) -> Path:
    """Path under get_data_root() with extra segments joined."""
    return get_data_root().joinpath(*parts)
