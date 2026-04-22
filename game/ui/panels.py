"""Small reusable panels: title/goodbye banners, legend, rack."""

from __future__ import annotations

from rich.align import Align
from rich.console import RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .styles import BONUS_STYLES, TILE_STYLE


def welcome_banner() -> Panel:
    """Title panel shown at game start."""
    title = Text("P Y T H O N   S C R A B B L E", style="bold bright_yellow")
    subtitle = Text("Command-line word battles", style="italic grey70")
    body = Align.center(Text.assemble(title, "\n", subtitle))
    return Panel(body, border_style="bright_magenta", padding=(1, 4))


def goodbye_banner() -> Panel:
    """Panel shown when a player quits."""
    body = Align.center(Text("Thanks for playing!", style="bold bright_cyan"))
    return Panel(body, border_style="bright_magenta", padding=(0, 4))


def legend() -> Panel:
    """Small legend explaining bonus-square colours."""
    table = Table.grid(padding=(0, 2))
    table.add_column()
    table.add_column()
    table.add_row(Text(" W ", style=BONUS_STYLES["W"]), Text("Triple word", style="grey70"))
    table.add_row(Text(" w ", style=BONUS_STYLES["w"]), Text("Double word", style="grey70"))
    table.add_row(Text(" L ", style=BONUS_STYLES["L"]), Text("Triple letter", style="grey70"))
    table.add_row(Text(" l ", style=BONUS_STYLES["l"]), Text("Double letter", style="grey70"))
    table.add_row(Text(" ★ ", style=BONUS_STYLES["*"]), Text("Start square", style="grey70"))
    return Panel(table, title="Legend", border_style="cyan", padding=(0, 1))


def rack_panel(tiles: list[str]) -> Panel:
    """Player's rack as a row of coloured tile cards."""
    body: RenderableType
    if not tiles:
        body = Text("(empty)", style="italic grey50")
    else:
        grid = Table.grid(padding=(0, 1))
        grid.add_row(*(
            Text(f" {t.upper() if t != '?' else '?'} ", style=TILE_STYLE)
            for t in tiles
        ))
        body = grid
    return Panel(
        body,
        title="[bold bright_yellow]Your rack[/]",
        border_style="bright_yellow",
        padding=(0, 1),
    )
