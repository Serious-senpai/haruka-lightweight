class TicTacToeException(Exception):
    pass


class StartError(TicTacToeException):
    pass


class MoveError(TicTacToeException):
    pass


class AlreadyStarted(StartError):
    pass


class NotEnoughPlayer(StartError):
    pass


class NotStarted(MoveError):
    pass


class InvalidMove(MoveError):
    pass


class InvalidTurn(MoveError):
    pass
