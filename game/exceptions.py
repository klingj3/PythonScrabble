class InvalidCoordinatesError(Exception):
    """Raised when invalid coordinate are provided"""
    def __init__(self, msg=None):
        if msg is None:
            msg = "Coordinates fall outside the bounds of the play area."
        super(InvalidCoordinatesError, self).__init__(msg)


class InvalidWordError(Exception):
    """Raised when an invalid word is attempted to be played"""
    def __init__(self, word, msg=None):
        if msg is None:
            msg = "Word %s is not valid." % word
        super(InvalidWordError, self).__init__(msg)
        self.word = word


class InvalidPlacementError(Exception):
    """ Raised when a played word does not align with tiles currently on the board."""
    def __init__(self, word, msg=None):
        if msg is None:
            msg = "Word %s cannot be played in the specified position" % word
        super(InvalidPlacementError, self).__init__(msg)
        self.word = word


class OutOfBoardError(Exception):
    """ Raised when a played word does not align with tiles currently on the board."""
    def __init__(self, word, msg=None):
        if msg is None:
            msg = "Placing word %s exceeds the boundaries of the board." % word
        super(OutOfBoardError, self).__init__(msg)
        self.word = word