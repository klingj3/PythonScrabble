"""Scoring, dictionary, and word validation."""

from __future__ import annotations

import json
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

from .exceptions import InvalidPlacementError
from .paths import data_path
from .types import BoardState, Move


_TRIE_CHILDREN_KEY = "_C"


def _annotate_trie_children(root: dict[str, Any]) -> None:
    """Cache each trie node's letter children as (index, child) pairs for fast walks."""
    a_ord = ord("A")
    stack: list[dict[str, Any]] = [root]
    while stack:
        node = stack.pop()
        if _TRIE_CHILDREN_KEY in node:
            continue
        children: list[tuple[int, dict[str, Any]]] = []
        for letter, child in node.items():
            if len(letter) == 1 and isinstance(child, dict):
                children.append((ord(letter) - a_ord, child))
                stack.append(child)
        node[_TRIE_CHILDREN_KEY] = tuple(children)


def _word_validity_checker(dictionary_root: dict[str, Any]) -> Callable[[str], bool]:
    """Trie lookup with a small LRU cache."""

    @lru_cache(maxsize=8192)
    def check(w_upper: str) -> bool:
        branch: dict[str, Any] = dictionary_root
        for character in w_upper:
            if character not in branch:
                return False
            branch = cast(dict[str, Any], branch[character])
        return bool(branch["VALID"])

    return check


class Rulebook:
    """Dictionary trie, English definitions, board bonuses, and move scoring."""

    def __init__(self) -> None:
        """Load tile scores, dictionary tree, and English lookup data."""
        self.board_special_tiles: list[str] = [
            "W  l   W   l  W",
            " w   L   L   w ",
            "  w   l l   w  ",
            "l  w   l   w  l",
            "    w     w    ",
            " L   L   L   L ",
            "  l   l l   l  ",
            "W  l   *   l  W",
            "  l   l l   l  ",
            " L   L   L   L ",
            "    w     w    ",
            "l  w   l   w  l",
            "  w   l l   w  ",
            " w   L   L   w ",
            "W  l   W   l  W",
        ]

        with open(data_path("tile_scores.json"), encoding="utf-8") as infile:
            self.tile_scores: dict[str, int] = json.loads(infile.read())

        self.dictionary_root: dict[str, Any] = self.generate_dictionary_tree()
        _annotate_trie_children(self.dictionary_root)
        self._check_word: Callable[[str], bool] = _word_validity_checker(self.dictionary_root)
        with open(data_path("english_dictionary.json"), encoding="utf-8") as infile:
            self.english_dictionary: dict[str, str] = json.loads(infile.read())

    def calculate_penalty(self, tiles: list[str]) -> int:
        """Sum face values of unplayed tiles (endgame penalty)."""
        return sum(self.tile_scores[tile] for tile in tiles)

    def define(self, word: str) -> str:
        """Definition text, or a short reason lookup failed."""
        word = word.upper()
        if not self.word_is_valid(word):
            return f"Word {word} does not appear in this game's list of scrabble words"
        definition = self.english_dictionary.get(word)
        if not definition:
            return f"Word {word} is in our Scrabble dictionary, but not in the English dictionary!"
        return f"{word}: {definition}"

    @staticmethod
    def generate_dictionary_tree(dict_path: str | Path | None = None) -> dict[str, Any]:
        """Load the packaged trie, or build one from a word list file."""
        default_txt = data_path("dictionary.txt")
        path = Path(dict_path) if dict_path is not None else default_txt
        path = path.resolve()

        if path == default_txt.resolve():
            with open(data_path("dictionary_tree.json"), encoding="utf-8") as infile:
                return cast(dict[str, Any], json.load(infile))

        with open(path, encoding="utf-8") as infile:
            dictionary_lines = [word[:-1] for word in infile]
        dictionary_tree: dict[str, Any] = {"VALID": False, "WORD": ""}
        for word in dictionary_lines:
            active_branch = dictionary_tree
            for i, character in enumerate(word):
                if character not in active_branch:
                    active_branch[character] = {"VALID": False, "WORD": active_branch["WORD"] + character}
                active_branch = cast(dict[str, Any], active_branch[character])
                if i == len(word) - 1:
                    active_branch["VALID"] = True

        return dictionary_tree

    def score_move(self, move: Move, board_state: BoardState, allow_illegal: bool = False) -> int:
        """Score the main word and cross-words, or return -1 if the placement is illegal."""

        def neighbor_x(y: int, x: int) -> bool:
            """True if (y, x) has a horizontal neighbor letter on the board."""
            return bool(
                (x > 0 and board_state[y][x - 1] != " ")
                or (x < 14 and board_state[y][x + 1] != " ")
            )

        def neighbor_y(y: int, x: int) -> bool:
            """True if (y, x) has a vertical neighbor letter on the board."""
            return bool(
                (y > 0 and board_state[y - 1][x] != " ")
                or (y < 14 and board_state[y + 1][x] != " ")
            )

        y, x = move.coords

        if allow_illegal or self.word_is_valid(move.word):
            total_score = self.score_word(y, x, move.dir, move.word, board_state)
        else:
            return -1

        is_d, is_r = int(move.dir == "D"), int(move.dir == "R")

        valid_position = False

        for i, tile in enumerate(move.word):
            if (y + i * is_d, x + i * is_r) == (7, 7):
                valid_position = True
            if move.dir == "D" and neighbor_x(y + i, x):
                valid_position = True
                if board_state[y + i][x] == " ":
                    word_start, word_end = x, x
                    while word_start > 0 and board_state[y + i][word_start - 1] != " ":
                        word_start -= 1
                    while word_end < 14 and board_state[y + i][word_end + 1] != " ":
                        word_end += 1
                    anc_word = (
                        board_state[y + i][word_start:x]
                        + tile
                        + board_state[y + i][x + 1 : word_end + 1]
                    )

                    if allow_illegal or self.word_is_valid(anc_word):
                        total_score += self.score_word(y + i, word_start, "R", anc_word, board_state)
                    else:
                        return -1
            elif move.dir == "R" and neighbor_y(y, x + i):
                valid_position = True
                if board_state[y][x + i] == " ":
                    word_start, word_end = y, y
                    while word_start > 0 and board_state[word_start - 1][x + i] != " ":
                        word_start -= 1
                    while word_end < 14 and board_state[word_end + 1][x + i] != " ":
                        word_end += 1
                    anc_word = "".join(
                        [
                            board_state[word_y][x + i] if word_y != y else tile
                            for word_y in range(word_start, word_end + 1)
                        ]
                    )

                    if allow_illegal or self.word_is_valid(anc_word):
                        total_score += self.score_word(word_start, x + i, "D", anc_word, board_state)
                    else:
                        return -1

        if not valid_position and not allow_illegal:
            return -1
        return total_score

    def score_word(self, y: int, x: int, direction: str, word: str, board_state: BoardState) -> int:
        """Score a single word segment with letter/word multipliers and the seven-tile bonus."""
        score = 0
        word_mul = 1

        assert direction == "R" or direction == "D"

        player_tiles_used = 0

        is_d, is_r = int(direction == "D"), int(direction == "R")

        for i, tile in enumerate(word):
            if tile.islower():
                tile = "?"

            board_curr_tile = board_state[y + i * is_d][x + i * is_r]

            if board_curr_tile != " ":
                if board_curr_tile != tile and not (board_curr_tile.islower() and tile == "?"):
                    raise InvalidPlacementError(
                        word=word, true_tile=board_curr_tile, attempted_tile=tile
                    )
                score += self.tile_scores[tile]
            else:
                player_tiles_used += 1

                spec_tile = self.board_special_tiles[y + i * is_d][x + i * is_r]
                if spec_tile == " ":
                    score += self.tile_scores[tile]
                else:
                    if spec_tile == "l":
                        score += self.tile_scores[tile] * 2
                    elif spec_tile == "L":
                        score += self.tile_scores[tile] * 3
                    else:
                        score += self.tile_scores[tile]
                        if spec_tile == "W":
                            word_mul *= 3
                        else:
                            word_mul *= 2

        score *= word_mul
        if player_tiles_used == 7:
            score += 50
        return score

    def word_is_valid(self, word: str) -> bool:
        """True if word is in the game dictionary."""
        return self._check_word(word.upper())
