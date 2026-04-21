"""Rich console, colours, and small UI helpers."""

from __future__ import annotations

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console: Console = Console(highlight=False)


# Premium-square palette; keys match Board.special_tiles encoding.
PREMIUM_STYLES: dict[str, str] = {
    "W": "bold white on red",       # Triple Word
    "w": "bold white on magenta",   # Double Word
    "L": "bold white on blue",      # Triple Letter
    "l": "bold white on cyan",      # Double Letter
    "*": "bold yellow on magenta",  # Center star
}

PREMIUM_GLYPHS: dict[str, str] = {
    "W": "W",
    "w": "w",
    "L": "L",
    "l": "l",
    "*": "★",
    " ": "·",
}


TILE_STYLE: str = "bold black on bright_yellow"
"""Style used for letters actually placed on the board."""

BLANK_TILE_STYLE: str = "bold black on bright_white"
"""Style for tiles played from a blank (lowercase letters)."""


def tile_cell(char: str) -> Text:
    """Render a played tile letter with the standard tile background."""
    if char.islower():
        return Text(f" {char.upper()} ", style=BLANK_TILE_STYLE)
    return Text(f" {char} ", style=TILE_STYLE)


def premium_cell(marker: str) -> Text:
    """Render a premium-square marker (or empty dot) with colour."""
    glyph = PREMIUM_GLYPHS.get(marker, "·")
    style = PREMIUM_STYLES.get(marker, "grey50")
    return Text(f" {glyph} ", style=style)


def welcome_banner() -> Panel:
    """Return the title panel shown at game start."""
    title = Text("P Y T H O N   S C R A B B L E", style="bold bright_yellow")
    subtitle = Text("Command-line word battles", style="italic grey70")
    body = Align.center(Text.assemble(title, "\n", subtitle))
    return Panel(body, border_style="bright_magenta", padding=(1, 4))


def goodbye_banner() -> Panel:
    """Return the panel shown when a player quits."""
    body = Align.center(Text("Thanks for playing!", style="bold bright_cyan"))
    return Panel(body, border_style="bright_magenta", padding=(0, 4))


def legend() -> Panel:
    """Small legend explaining premium square colours."""
    table = Table.grid(padding=(0, 2))
    table.add_column()
    table.add_column()
    table.add_row(Text(" W ", style=PREMIUM_STYLES["W"]), Text("Triple word", style="grey70"))
    table.add_row(Text(" w ", style=PREMIUM_STYLES["w"]), Text("Double word", style="grey70"))
    table.add_row(Text(" L ", style=PREMIUM_STYLES["L"]), Text("Triple letter", style="grey70"))
    table.add_row(Text(" l ", style=PREMIUM_STYLES["l"]), Text("Double letter", style="grey70"))
    table.add_row(Text(" ★ ", style=PREMIUM_STYLES["*"]), Text("Start square", style="grey70"))
    return Panel(table, title="Legend", border_style="cyan", padding=(0, 1))


def info(message: str) -> None:
    """Print a neutral informational message."""
    console.print(f"[bright_blue]ℹ[/] {message}")


def success(message: str) -> None:
    """Print a success/positive message."""
    console.print(f"[bright_green]✓[/] {message}")


def warn(message: str) -> None:
    """Print a warning/invalid-input message."""
    console.print(f"[bright_yellow]![/] {message}")


def error(message: str) -> None:
    """Print an error message."""
    console.print(f"[bright_red]✗[/] {message}")
