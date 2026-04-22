"""Tile bag: draw and exchange tiles."""

from __future__ import annotations

import json
import random
import sys
from collections import Counter

from .paths import data_path


class TileBag:
    """Shuffled pool of letter tiles drawn by players."""

    def __init__(self) -> None:
        """Load letter counts from tile_counts.json."""
        with open(data_path("tile_counts.json"), encoding="utf-8") as infile:
            self.tile_counts: dict[str, int] = json.load(infile)

        self.bag: list[str] = []
        for letter, count in self.tile_counts.items():
            self.bag += [letter for _ in range(count)]

    def __str__(self) -> str:
        """Return a comma-separated count listing (blank tile shown last)."""
        pairs = sorted(Counter(self.bag).items(), key=lambda x: x[0])
        pairs = pairs[1:] + pairs[:1]
        return ", ".join([letter + ": " + str(count) for letter, count in pairs])

    def grab(self, num_tiles: int) -> list[str]:
        """Shuffle the bag, then take up to num_tiles from the front."""
        random.shuffle(self.bag)
        new_tiles, self.bag = self.bag[:num_tiles], self.bag[num_tiles:]
        return new_tiles

    def switch(self, discarded_tiles: list[str]) -> list[str]:
        """Swap discarded tiles for new draws if the bag has enough left; else return them unchanged."""
        if len(self.bag) <= 7:
            sys.stderr.write("ERROR: Tiles can only be exchanged when there are more than 7 tiles in the bag.")
            return discarded_tiles

        new_tiles = self.grab(len(discarded_tiles))
        self.bag += discarded_tiles

        return new_tiles
