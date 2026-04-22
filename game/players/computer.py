"""Computer opponent: exhaustive move search."""

from __future__ import annotations

from typing import Any, NamedTuple

from ..rulebook import Rulebook
from ..types import BoardState, Move
from .base import Player

_A_ORD = ord("A")
_BLANK_IDX = 26
_RACK_VEC_LEN = 27
_TRIE_CHILDREN_KEY = "_C"


def _find_words_dfs(
    node: dict[str, Any],
    counts: list[int],
    fixed_at: list[str | None],
    pos: int,
    rack_used: int,
    blank_mask: int,
    min_length: int,
    max_length: int,
    out: list[str],
) -> None:
    """Depth-first trie walk: append finished words to out. counts and fixed_at are updated in place."""
    if (
        node["VALID"]
        and pos >= min_length
        and rack_used > 0
        and fixed_at[pos] is None
    ):
        word: str = node["WORD"]
        if blank_mask:
            word = "".join(
                c.lower() if (blank_mask >> i) & 1 else c for i, c in enumerate(word)
            )
        out.append(word)

    if pos >= max_length:
        return

    forced = fixed_at[pos]
    if forced is not None:
        child = node.get(forced)
        if child is not None:
            _find_words_dfs(
                child, counts, fixed_at, pos + 1, rack_used, blank_mask,
                min_length, max_length, out,
            )
        return

    for idx, child in node[_TRIE_CHILDREN_KEY]:
        if counts[idx] > 0:
            counts[idx] -= 1
            _find_words_dfs(
                child, counts, fixed_at, pos + 1, rack_used + 1, blank_mask,
                min_length, max_length, out,
            )
            counts[idx] += 1
        if counts[_BLANK_IDX] > 0:
            counts[_BLANK_IDX] -= 1
            _find_words_dfs(
                child, counts, fixed_at, pos + 1, rack_used + 1,
                blank_mask | (1 << pos), min_length, max_length, out,
            )
            counts[_BLANK_IDX] += 1


class _MoveParam(NamedTuple):
    """One candidate anchor: position, direction, length bounds, and board-fixed letters."""

    coords: tuple[int, int]
    dir: str
    min_len: int
    max_len: int
    fixed: list[tuple[str, int]]


class ComputerPlayer(Player):
    """Computer opponent: search legal words and keep the best score."""

    def __init__(
        self,
        player_id: int,
        init_tiles: list[str],
        rulebook: Rulebook,
        name: str | None = None,
    ) -> None:
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
        """Words from the rack, optional fixed board letters, and length bounds."""
        if pos > max_length:
            return []

        if tiles is None:
            tiles = self.tiles
        if starting_branch is None:
            starting_branch = self.rulebook.dictionary_root

        assert len(fixed_tiles) <= 1 or all(
            fixed_tiles[i][1] < fixed_tiles[i + 1][1] for i in range(len(fixed_tiles) - 1)
        )

        counts = [0] * _RACK_VEC_LEN
        for tile in tiles:
            if tile == "?":
                counts[_BLANK_IDX] += 1
            else:
                counts[ord(tile) - _A_ORD] += 1

        max_fixed_pos = max((p for _, p in fixed_tiles), default=-1)
        fixed_at: list[str | None] = [None] * (max(max_length, max_fixed_pos) + 2)
        for letter, fp in fixed_tiles:
            fixed_at[fp] = letter

        out: list[str] = []
        _find_words_dfs(
            starting_branch,
            counts,
            fixed_at,
            pos,
            0,
            0,
            min_length,
            max_length,
            out,
        )
        return out

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

    def get_move(
        self,
        board_state: BoardState,
        board: Board | None = None,
        *,
        scores: list[tuple[str, int]] | None = None,
        turn: int | None = None,
    ) -> Move:
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
        """Rulebook score for this move on the given board."""
        return self.rulebook.score_move(move, board_state)
