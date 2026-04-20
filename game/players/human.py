"""Human player CLI input."""

from __future__ import annotations

from ..exceptions import InvalidPlacementError, QuitGame
from ..rulebook import Rulebook
from ..types import BoardState, Move
from .base import Player


class HumanPlayer(Player):
    """Interactive player reading commands from stdin."""

    def __init__(
        self,
        player_id: int,
        init_tiles: list[str],
        rulebook: Rulebook,
        name: str | None = None,
    ) -> None:
        """See ``Player``; ``name`` avoids the interactive name prompt when set."""
        super().__init__(player_id, init_tiles, rulebook, name)

    def get_move(self, board_state: BoardState) -> Move:
        """Parse stdin until a valid skip, exchange, or word play (or raise ``QuitGame``)."""

        def tiles_present_for_move(move: Move) -> bool:
            """Return whether the rack can supply blank/new squares for ``move``."""
            tile_copy = self.tiles.copy()
            is_d, is_r = (move.dir == "D", move.dir == "R")
            y, x = move.coords

            if max(y + is_d * len(move.word), x + is_r * len(move.word)) > 14:
                return False

            for i, tile in enumerate(move.word.upper()):
                if move.coords == (-2, -2) or board_state[y + i * is_d][x + i * is_r] == " ":
                    if tile not in self.tiles and "?" in self.tiles:
                        tile = "?"
                    try:
                        tile_copy.remove(tile)
                    except ValueError:
                        return False
            return True

        print("Tiles: [" + str(self.tiles) + "]")
        while True:
            player_move = input("Action: ")
            move_segments = player_move.lower().strip().split(" ")

            if len(move_segments) == 1:
                if move_segments[0] == "skip":
                    return Move((-1, -1), "", "")
                if move_segments[0] == "quit":
                    raise QuitGame()
                if move_segments[0] == "help":
                    print(
                        "\n".join(
                            [
                                "Commands:",
                                "'quit' quits the game",
                                "'skip' skips a turn",
                                "'exchange' <LETTERS> exchanges some of your tiles",
                                "'define' <WORD> will define a word previously played",
                                "'<X> <Y> <D or R> <WORD>' (e.g 7 7 R PYTHON) plays the word in the direction "
                                "R for right (or D for down), starting at x, y coordinates 7, 7",
                            ]
                        )
                    )
                else:
                    print("Command {} not recognized.".format(move_segments[0]))
            elif len(move_segments) == 2:
                if move_segments[0] == "exchange":
                    if tiles_present_for_move(Move((-2, -2), "", move_segments[1].upper())):
                        return Move((-2, -2), "", move_segments[1])
                    print("Tiles for this exchange are not present in your rack.")
                elif move_segments[0] == "define":
                    print(self.rulebook.define(move_segments[1]))
            elif len(move_segments) == 4:
                sx, sy, direction, word = move_segments
                direction = direction.upper()

                move = Move((int(sy, 16), int(sx, 16)), direction, word.upper())
                row, col = move.coords
                if row < 0 or row > 14 or col < 0 or col > 14:
                    print("Moves must be within the boundaries 0 and d (d being hexadecimal 14)")
                elif direction != "D" and direction != "R":
                    print(
                        "direction argument in format <x> <y> <dir> <tiles> must be D or R, not "
                        + direction
                    )
                else:
                    try:
                        if not tiles_present_for_move(move):
                            print("The player's tile rack does not contain the tiles needed for this move.")
                        elif self.rulebook.score_move(move, board_state) < 0:
                            print(
                                "This word, or an ancillary word formed, is invalid, or the word does not border "
                                "an existing tile on the board."
                            )
                        else:
                            return move
                    except InvalidPlacementError as exc:
                        print(exc)
            else:
                print("Command {} not recognized. Type 'help' for help".format(move_segments[0]))
