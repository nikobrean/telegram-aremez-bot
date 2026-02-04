class GameError(Exception):
    """Базовая ошибка игры."""
    pass


class SessionNotFound(GameError):
    pass


class SessionAlreadyStarted(GameError):
    pass


class PlayerAlreadyJoined(GameError):
    pass


class SessionFull(GameError):
    pass


class NotEnoughPlayers(GameError):
    pass


class NotOwner(GameError):
    pass
