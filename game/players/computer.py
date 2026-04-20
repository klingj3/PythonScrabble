"""Computer opponent: exhaustive move search."""

from __future__ import annotations

from typing import Any, NamedTuple

from ..rulebook import Rulebook
from ..types import BoardState, Move
from .base import Player


class _MoveParam(NamedTuple):
    """One candidate anchor: position, direction, length bounds, and board-fixed letters."""

    coords: tuple[int, int]
    dir: str
    min_len: int
    max_len: int
    fixed: list[tuple[str, int]]


class ComputerPlayer(Player):
    """AI that enumerates dictionary words and picks the highest-scoring legal move."""

    def __init__(
        self,
        player_id: int,
        init_tiles: list[str],
        rulebook: Rulebook,
        name: str | None = None,
    ) -> None:
        """See ``Player``."""
        super().__init__(player_id, init_tiles, rulebook, name)

    def find_words(
        self,
        tiles: list[str] | None = None,
        starting_branch: dict[str, Any] | None = None,
        fixed_tiles: tuple[tuple[str, int], ...] = (),
        pos: int = 0,
        min_length: int = 2,
        max_length: int = 15,
    ) -> list[str]:
        """Enumerate valid words from the rack, optional fixed board letters, and length bounds."""
        if pos > max_length:
            return []

        if tiles is None:
            tiles = self.tiles.copy()
        if starting_branch is None:
            starting_branch = self.rulebook.dictionary_root

        assert len(fixed_tiles) == 1 or all(
            fixed_tiles[i][1] < fixed_tiles[i + 1][1] for i in range(len(fixed_tiles) - 1)
        )

        if (
            starting_branch["VALID"]
            and len(starting_branch["WORD"]) >= min_length
            and len(tiles) < len(self.tiles)
        ):
            if not fixed_tiles or fixed_tiles[0][1] > len(starting_branch["WORD"]):
                valid_words = [starting_branch["WORD"]]
            else:
                valid_words = []
        else:
            valid_words = []

        if fixed_tiles and fixed_tiles[0][1] == pos:
            if fixed_tiles[0][0] in starting_branch:
                valid_words += self.find_words(
                    tiles=tiles,
                    starting_branch=starting_branch[fixed_tiles[0][0]],
                    fixed_tiles=fixed_tiles[1:],
                    pos=pos + 1,
                    min_length=min_length,
                    max_length=max_length,
                )
        else:
            for tile in set(tiles):
                new_tiles = tiles.copy()
                new_tiles.remove(tile)
                if tile == "?":
                    words_with_blanks: list[str] = []
                    for key, value in starting_branch.items():
                        if key != "VALID" and key != "WORD":
                            words_with_blanks += self.find_words(
                                tiles=new_tiles,
                                starting_branch=value,
                                pos=pos + 1,
                                min_length=min_length,
                                max_length=max_length,
                                fixed_tiles=fixed_tiles,
                            )
                    words_with_blanks = [
                        word[:pos] + word[pos].lower() + word[pos + 1 :] for word in words_with_blanks
                    ]
                    valid_words += words_with_blanks
                elif tile in starting_branch:
                    valid_words += self.find_words(
                        tiles=new_tiles,
                        starting_branch=starting_branch[tile],
                        pos=pos + 1,
                        min_length=min_length,
                        max_length=max_length,
                        fixed_tiles=fixed_tiles,
                    )

        return valid_words

    def get_move_params(
        self, coords: tuple[int, int], direction: str, board_state: BoardState
    ) -> tuple[int, list[tuple[str, int]]]:
        """Return minimum prefix length before legality and board-fixed letter positions, or (-1, [])."""

        def is_island(y: int, x: int) -> bool:
            """True when (y, x) has no orthogonal neighbor tiles (except opening at the star)."""
            if (y, x) == (7, 7):
                return False

            min_x, max_x = max(x - 1, 0), min(x + 1, 14)
            min_y, max_y = max(y - 1, 0), min(y + 1, 14)
            for near_y in range(min_y, max_y + 1):
                if board_state[near_y][x] != " ":
                    return False
            for near_x in range(min_x, max_x + 1):
                if board_state[y][near_x] != " ":
                    return False
            return True

        assert direction == "D" or direction == "R"

        start_y, start_x = coords
        y, x = coords
        fixed_tiles: list[tuple[str, int]] = []
        tiles_rem = len(self.tiles)

        tiles_to_validity = -1

        if direction == "D":
            if y > 0 and board_state[y - 1][x] != " ":
                return -1, []

            while y < 15 and (tiles_rem or board_state[y][x] != " "):
                if tiles_to_validity == -1:
                    if not is_island(y, x):
                        tiles_to_validity = y - start_y + 1
                if board_state[y][x] == " ":
                    tiles_rem -= 1
                else:
                    fixed_tiles.append((board_state[y][x], y - start_y))
                y += 1
            return tiles_to_validity, fixed_tiles

        if x > 0 and board_state[y][x - 1] != " ":
            return -1, []

        while x < 15 and (tiles_rem or board_state[y][x] != " "):
            if tiles_to_validity == -1:
                if not is_island(y, x):
                    tiles_to_validity = x - start_x + 1
            if board_state[y][x] == " ":
                tiles_rem -= 1
            else:
                fixed_tiles.append((board_state[y][x], x - start_x))
            x += 1
        return tiles_to_validity, fixed_tiles

    def get_valid_locations(self, board_state: BoardState) -> list[_MoveParam]:
        """List every anchor square and direction where a word may legally start."""
        valid_move_params: list[_MoveParam] = []

        for y in range(15):
            for x in range(15):
                for direction in ["D", "R"]:
                    min_len, fixed_tiles = self.get_move_params((y, x), direction, board_state)
                    if min_len != -1:
                        if direction == "D":
                            valid_move_params.append(
                                _MoveParam((y, x), direction, min_len, 15 - y, fixed_tiles)
                            )
                        else:
                            valid_move_params.append(
                                _MoveParam((y, x), direction, min_len, 15 - x, fixed_tiles)
                            )

        return valid_move_params

    def get_move(self, board_state: BoardState) -> Move:
        """Choose the highest-scoring valid move or pass when none score positively."""
        valid_locations = self.get_valid_locations(board_state)

        valid_moves: list[Move] = []
        for vl in valid_locations:
            valid_words = self.find_words(
                fixed_tiles=tuple(vl.fixed),
                min_length=max(2, vl.min_len),
                max_length=vl.max_len,
            )
            valid_moves += [Move(vl.coords, vl.dir, word) for word in valid_words]

        move_scores = [(move, self.move_heuristic(move, board_state)) for move in valid_moves]
        move_scores = sorted(move_scores, key=lambda x: x[1], reverse=True)

        if move_scores and move_scores[0][1] > 0:
            best = move_scores[0][0]
            self.word_hist.append(best.word)
            self.score_hist.append(move_scores[0][1])
            return best
        return Move((-1, -1), "", "")

    def move_heuristic(self, move: Move, board_state: BoardState) -> int:
        """Score ``move`` with the shared rulebook (same as move quality)."""
        return self.rulebook.score_move(move, board_state)
