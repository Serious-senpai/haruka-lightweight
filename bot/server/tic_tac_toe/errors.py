from __future__ import annotations

from typing import TYPE_CHECKING


class TicTacToeException(Exception):
    """Base class for all exceptions from this module"""
    pass


class StartError(TicTacToeException):
    """Exceptions raised when attempting to start a game"""
    pass


class AlreadyStarted(StartError):
    """The game was started before"""
    pass


class NotEnoughPlayer(StartError):
    """Not enough players to start the game"""
    pass


class MissingPermission(StartError):
    """Player does not have permission to start the game"""
    pass


class MoveError(TicTacToeException):
    """Exceptions raised when attempting to make a move"""
    pass


class AlreadyEnded(MoveError):
    """Game has already ended"""
    pass


class NotStarted(MoveError):
    """Game hasn't started yet"""
    pass


class InvalidMove(MoveError):
    """Invalid row/column provided when attempting to make a move"""
    pass


class InvalidTurn(MoveError):
    """Players trying to make a move when it hasn't been their turn
    yet.

    Attributes
    -----
    is_spectator: ``bool``
        Whether the player is a spectator
    """

    __slots__ = (
        "is_spectator",
    )
    if TYPE_CHECKING:
        is_spectator: bool

    def __init__(self, *, is_spectator: bool) -> None:
        self.is_spectator = is_spectator
