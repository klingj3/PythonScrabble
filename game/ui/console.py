"""Shared Rich console and short feedback helpers."""

from __future__ import annotations

from rich.console import Console

console: Console = Console(highlight=False)


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
