"""Data path resolution."""

from __future__ import annotations

import os
from pathlib import Path
from unittest import TestCase

from game.paths import data_path, get_data_root


class TestPaths(TestCase):
    def test_default_data_path_exists(self) -> None:
        p = data_path("tile_scores.json")
        self.assertTrue(p.is_file(), msg=f"missing {p}")

    def test_data_root_env_respected(self) -> None:
        expected = Path(__file__).resolve().parents[1] / "game" / "data"
        self.assertEqual(get_data_root(), expected)

    def test_data_root_override(self) -> None:
        expected = get_data_root()
        previous = os.environ.get("DATA_ROOT")
        os.environ["DATA_ROOT"] = str(expected)
        try:
            self.assertEqual(get_data_root(), expected)
        finally:
            if previous is None:
                os.environ.pop("DATA_ROOT", None)
            else:
                os.environ["DATA_ROOT"] = previous
