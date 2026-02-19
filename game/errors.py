class GameError(Exception):
    pass


class SessionNotFound(GameError):
    pass


class SessionAlreadyExists(GameError):
    pass


class PlayerAlreadyJoined(GameError):
    pass


class SessionFull(GameError):
    pass


class NotOwner(GameError):
    pass


class NotEnoughPlayers(GameError):
    pass


class SessionAlreadyStarted(GameError):
    pass
