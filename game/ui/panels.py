"""Small reusable panels: title/goodbye banners, legend, rack."""

from __future__ import annotations

import json
import time

from rich.align import Align
from rich.console import RenderableType
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..paths import data_path
from .console import console
from .styles import BONUS_STYLES, TILE_STYLE

_TILE_SCORES: dict[str, int] = json.loads(data_path("tile_scores.json").read_text())

_SQUABBLE_LETTERS: tuple[str, ...] = tuple("SQUABBLE")
_SPLASH_BORDERS: tuple[str, ...] = (
    "bright_magenta",
    "magenta3",
    "purple",
    "bright_cyan",
    "cyan",
    "deep_sky_blue1",
)


def _squabble_tile_word(visible: int) -> Text:
    """Type-on title using tile styling to match rack tile visuals."""
    n = max(0, min(visible, len(_SQUABBLE_LETTERS)))
    parts: list[Text | str] = []
    for i, ch in enumerate(_SQUABBLE_LETTERS):
        style = TILE_STYLE if i < n else "grey35 on grey19"
        parts.append(Text(f" {ch} ", style=style))
        if i < len(_SQUABBLE_LETTERS) - 1:
            parts.append(Text(" "))
    return Text.assemble(*parts) if parts else Text("")


def _final_splash_panel() -> Panel:
    """Static final frame shown after the splash animation."""
    title = _squabble_tile_word(len(_SQUABBLE_LETTERS))
    subtitle = Text("Cross-word building word tile game", style="italic grey70")
    body = Align.center(Text.assemble(title, "\n", subtitle))
    return Panel(body, border_style="bright_magenta", padding=(1, 4))


def _splash_viewport(panel: Panel) -> RenderableType:
    """Place the splash panel in the middle of the terminal (horizontal + vertical)."""
    h = console.height
    if h is None or h < 10:
        h = 24
    return Align.center(panel, vertical="middle", height=h)


def show_launch_splash(
    *,
    frame_delay: float = 0.05,
    hold_final: float = 0.75,
) -> None:
    """Animated SQUABBLE splash using tile-style type-on and rainbow borders."""
    console.clear()
    subtitle_dim = Text("Cross-word building word tile game", style="italic grey42")
    subtitle_full = Text("Cross-word building word tile game", style="italic grey78")

    def frame(step: int) -> RenderableType:
        border = _SPLASH_BORDERS[step % len(_SPLASH_BORDERS)]
        title = _squabble_tile_word(step + 1)
        sub = subtitle_dim if step < len(_SQUABBLE_LETTERS) // 2 else subtitle_full
        body = Align.center(Text.assemble(title, "\n", sub))
        panel = Panel(body, border_style=border, padding=(1, 4))
        return _splash_viewport(panel)

    total_steps = len(_SQUABBLE_LETTERS) + 12
    with Live(
        frame(0),
        console=console,
        refresh_per_second=60,
        transient=False,
    ) as live:
        time.sleep(frame_delay)
        for s in range(1, total_steps):
            live.update(frame(s), refresh=True)
            time.sleep(frame_delay)
        live.update(_splash_viewport(_final_splash_panel()), refresh=True)
        time.sleep(hold_final)
    console.clear()

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


def rack_panel(tiles: list[str], used_indices: set[int] | None = None) -> Panel:
    """Player's rack as a row of coloured tile cards with point values below."""
    body: RenderableType
    if not tiles:
        body = Text("(empty)", style="italic grey50")
    else:
        grid = Table.grid(padding=(0, 1))
        letter_cells: list[Text] = []
        score_cells: list[Text] = []
        for i, t in enumerate(tiles):
            is_used = bool(used_indices and i in used_indices)
            letter_cells.append(Text(
                f" {t.upper() if t != '?' else '?'} ",
                style="bold grey35 on grey19" if is_used else TILE_STYLE,
            ))
            score = _TILE_SCORES.get(t.upper(), 0)
            score_cells.append(Text(
                f" {score} ",
                style="grey35" if is_used else "grey70",
            ))
        grid.add_row(*letter_cells)
        grid.add_row(*score_cells)
        body = grid
    return Panel(
        body,
        title="[bold bright_yellow]Your rack[/]",
        border_style="bright_yellow",
        padding=(0, 1),
    )
