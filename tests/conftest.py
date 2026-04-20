"""Ensure DATA_ROOT resolves before any game imports."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("DATA_ROOT", str(ROOT / "game" / "data"))
