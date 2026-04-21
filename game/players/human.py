"""Human player CLI input with live board highlights during entry."""

from __future__ import annotations

import sys
from collections.abc import Generator

from rich.console import Group, RenderableType
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from ..board import Board, Highlight
from ..exceptions import InvalidPlacementError, QuitGame
from ..rulebook import Rulebook
from ..types import BoardState, Move
from ..ui import TILE_STYLE, console, warn
from .base import Player


def _rack(tiles: list[str]) -> Panel:
    """Render the player's rack as a row of coloured tile cards."""
    body: RenderableType
    if not tiles:
        body = Text("(empty)", style="italic grey50")
    else:
        grid = Table.grid(padding=(0, 1))
        grid.add_row(*(Text(f" {t.upper() if t != '?' else '?'} ", style=TILE_STYLE) for t in tiles))
        body = grid
    return Panel(body, title="[bold bright_yellow]Your rack[/]",
                 border_style="bright_yellow", padding=(0, 1))


_HELP_LINES = (
    "quit                    leave the game",
    "skip                    pass the turn",
    "exchange <LETTERS>      trade tiles for new ones",
    "define <WORD>           look up a definition",
    "<x> <y> <R|D> <WORD>    play a word  (e.g. 7 7 R PYTHON)",
)


def _parse_highlight(buf: str) -> Highlight:
    """Derive column / row / word-path highlights from an in-progress input buffer."""
    stripped = buf.lstrip().lower()
    if stripped.startswith(("define", "exchange", "skip", "quit", "help")):
        return Highlight()

    tokens = buf.split()
    trailing = bool(buf) and buf[-1].isspace()
    if not tokens:
        return Highlight()

    def coord(tok: str) -> int | None:
        try:
            v = int(tok, 16)
        except ValueError:
            return None
        return v if 0 <= v <= 14 else None

    col = coord(tokens[0])
    if col is None:
        return Highlight()
    if len(tokens) == 1 and not trailing:
        return Highlight(col=col)

    row = coord(tokens[1]) if len(tokens) >= 2 else None
    if row is None:
        return Highlight(col=col)
    if len(tokens) == 2 and not trailing:
        return Highlight(col=col, row=row)

    direction = tokens[2][0].upper() if len(tokens) >= 3 and tokens[2] else ""
    if direction not in ("R", "D"):
        return Highlight(col=col, row=row)

    word = tokens[3] if len(tokens) >= 4 else ""
    path = tuple(
        (row + k if direction == "D" else row,
         col + k if direction == "R" else col,
         ch.upper())
        for k, ch in enumerate(word)
        if ch.isalpha()
        and 0 <= (row + k if direction == "D" else row) < 15
        and 0 <= (col + k if direction == "R" else col) < 15
    )
    return Highlight(col=col, row=row, path=path)


class HumanPlayer(Player):
    """Interactive player reading commands from stdin."""

    def __init__(
        self,
        player_id: int,
        init_tiles: list[str],
        rulebook: Rulebook,
        name: str | None = None,
    ) -> None:
        """If name is given, skip asking for it on stdin."""
        super().__init__(player_id, init_tiles, rulebook, name)

    def get_move(self, board_state: BoardState, board: object | None = None) -> Move:
        """Read stdin until a valid move; QuitGame means the player quit."""
        typed_board = board if isinstance(board, Board) else None
        if typed_board is not None and sys.stdin.isatty():
            return self._tty_get_move(typed_board, board_state)

        err: str | None = None
        while True:
            console.print(_rack(self.tiles))
            if err:
                warn(err)
            line = Prompt.ask("[bold bright_green]Action[/]", console=console)
            err = None
            segments = line.lower().strip().split()
            if not segments:
                continue
            result = self._interpret(segments, board_state)
            if isinstance(result, Move):
                return result
            err = "\n".join(_HELP_LINES) if result == "help" else result

    def _tty_get_move(self, board: Board, board_state: BoardState) -> Move:
        """TTY path: one Rich Live session for typing, errors, and the board."""
        buf = ""
        message: str | None = None

        def render() -> RenderableType:
            board.highlight = _parse_highlight(buf)
            pieces: list[RenderableType] = [board, _rack(self.tiles)]
            if message:
                pieces.append(Panel(message, title="[bold bright_cyan]Message[/]",
                                    border_style="cyan", padding=(0, 1)))
            pieces.append(Text.assemble(("Action: ", "bold bright_green"),
                                        (buf, "bright_white")))
            return Group(*pieces)

        keys = _keystrokes()
        try:
            with Live(render(), console=console, auto_refresh=False,
                      transient=False) as live:
                while True:
                    for ch in keys:
                        if ch in ("\r", "\n"):
                            break
                        if ch in ("\x7f", "\x08"):
                            buf = buf[:-1]
                        elif ch.isprintable():
                            buf += ch
                        live.update(render(), refresh=True)

                    segments = buf.lower().strip().split()
                    buf = ""
                    if not segments:
                        live.update(render(), refresh=True)
                        continue
                    result = self._interpret(segments, board_state)
                    if isinstance(result, Move):
                        return result
                    message = "\n".join(_HELP_LINES) if result == "help" else result
                    live.update(render(), refresh=True)
        finally:
            keys.close()
            board.highlight = None

    def _interpret(self, segments: list[str], board_state: BoardState) -> Move | str:
        """Parse tokens into a Move, the string "help", or an error message."""
        if len(segments) == 1:
            if segments[0] == "skip":
                return Move((-1, -1), "", "")
            if segments[0] == "quit":
                raise QuitGame()
            if segments[0] == "help":
                return "help"
            return f"Command '{segments[0]}' not recognized. Type 'help' for help."

        if len(segments) == 2 and segments[0] == "exchange":
            letters = segments[1].upper()
            if self._tiles_present(Move((-2, -2), "", letters), board_state):
                return Move((-2, -2), "", letters)
            return "Tiles for this exchange are not present in your rack."
        if len(segments) == 2 and segments[0] == "define":
            return self.rulebook.define(segments[1])

        if len(segments) != 4:
            return f"Command '{segments[0]}' not recognized. Type 'help' for help."

        sx, sy, direction, word = segments
        direction = direction.upper()
        try:
            move = Move((int(sy, 16), int(sx, 16)), direction, word.upper())
        except ValueError:
            return "Coordinates must be hex digits 0–d (e.g. 7, a, d)."
        row, col = move.coords
        if not (0 <= row <= 14 and 0 <= col <= 14):
            return "Moves must be within the boundaries 0 and d (d being hexadecimal 14)."
        if direction not in ("D", "R"):
            return f"Direction must be D or R, not {direction}."
        try:
            if not self._tiles_present(move, board_state):
                return "Your rack does not contain the tiles needed for this move."
            if self.rulebook.score_move(move, board_state) < 0:
                return ("This word, or an ancillary word formed, is invalid, or the word "
                        "does not border an existing tile on the board.")
        except InvalidPlacementError as exc:
            return str(exc)
        return move

    def _tiles_present(self, move: Move, board_state: BoardState) -> bool:
        """True if the rack can cover every empty square this play needs."""
        rack = self.tiles.copy()
        is_d, is_r = move.dir == "D", move.dir == "R"
        y, x = move.coords
        wlen = len(move.word)
        if wlen and max(y + is_d * (wlen - 1), x + is_r * (wlen - 1)) > 14:
            return False
        for i, tile in enumerate(move.word.upper()):
            if move.coords == (-2, -2) or board_state[y + i * is_d][x + i * is_r] == " ":
                if tile not in rack and "?" in rack:
                    tile = "?"
                try:
                    rack.remove(tile)
                except ValueError:
                    return False
        return True


def _keystrokes() -> Generator[str, None, None]:
    """Yield one character at a time from raw stdin."""
    if sys.platform == "win32":
        import msvcrt
        getwch = msvcrt.getwch  # type: ignore[attr-defined]
        while True:
            ch = getwch()
            if ord(ch) in (0, 224):
                getwch()
                continue
            yield ch
    else:
        import termios
        import tty

        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            while True:
                ch = sys.stdin.read(1)
                if ch == "\x1b":
                    import select
                    if select.select([sys.stdin], [], [], 0)[0]:
                        sys.stdin.read(2)
                    continue
                if ch == "\x03":
                    raise KeyboardInterrupt
                yield ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
