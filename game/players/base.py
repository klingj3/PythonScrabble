"""Abstract player and shared move handling."""

from __future__ import annotations

from ..rulebook import Rulebook
from ..types import BoardState, Move


class Player:
    """Common player state: rack, rulebook, and optional score/word history."""

    def __init__(
        self,
        player_id: int,
        init_tiles: list[str],
        rulebook: Rulebook,
        name: str | None = None,
    ) -> None:
        while name is None:
            name = input("Enter the name for human {}: ".format(player_id))
            if name.isspace():
                print("Player names must contain non-space characters.")
                name = None
        self.name = name
        self.id = player_id
        self.score_hist: list[int] = []
        self.word_hist: list[str] = []
        self.tiles: list[str] = init_tiles
        self.rulebook = rulebook

    def __str__(self) -> str:
        """Return the player's display name."""
        return self.name

    def get_move(self, board_state: BoardState, board: object | None = None) -> Move:
        """Return the next move (subclasses implement interaction or search)."""
        raise NotImplementedError

    def prompt_move(self, board_state: BoardState, board: object | None = None) -> Move:
        """Obtain a move and remove spent tiles from the rack when applicable."""

        def remove_used_tiles(move: Move) -> None:
            """Remove tiles spent on this play or exchange from the rack."""
            coords, word, direction = move.coords, move.word, move.dir

            if coords == (-2, -2):
                for tile in move.word:
                    self.tiles.remove(tile)
            else:
                is_d, is_r = (direction == "D", direction == "R")
                y, x = coords
                for i, tile in enumerate(word.upper()):
                    if board_state[y + i * is_d][x + i * is_r] == " ":
                        if tile not in self.tiles and "?" in self.tiles:
                            tile = "?"
                        self.tiles.remove(tile)

        move = self.get_move(board_state, board=board)

        if move.coords != (-1, -1):
            remove_used_tiles(move)

        return move

    def receive_tiles(self, new_tiles: list[str]) -> None:
        """Append newly drawn tiles to the rack."""
        self.tiles += new_tiles

    def set_tiles(self, tiles: list[str]) -> None:
        """Replace the rack (testing or setup)."""
        self.tiles = tiles
