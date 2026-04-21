"""Domain-specific exceptions for board and CLI flow."""

from __future__ import annotations


class InvalidCoordinatesError(Exception):
    """Raised when coordinates fall outside the board."""

    def __init__(self, msg: str | None = None) -> None:
        """Default message if msg is omitted."""
        if msg is None:
            msg = "Coordinates fall outside the bounds of the play area."
        super().__init__(msg)


class InvalidWordError(Exception):
    """Raised when a word is not in the Scrabble dictionary."""

    def __init__(self, word: str, msg: str | None = None) -> None:
        """Store word; optional custom message."""
        if msg is None:
            msg = "Word %s is not valid." % word
        super().__init__(msg)
        self.word = word


class InvalidPlacementError(Exception):
    """Raised when a play conflicts with letters already on the board."""

    def __init__(
        self,
        *,
        word: str,
        msg: str | None = None,
        true_tile: str | None = None,
        attempted_tile: str | None = None,
    ) -> None:
        """Optional detail when the board letter and played letter disagree."""
        if msg is None:
            msg = "Word %s cannot be played in the specified position" % word
            if true_tile is not None and attempted_tile is not None:
                msg += "\n{} exists at this point, while {} was attempted".format(true_tile, attempted_tile)
        super().__init__(msg)
        self.word = word


class QuitGame(Exception):
    """Human chose quit; the CLI catches this."""
