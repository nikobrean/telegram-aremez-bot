import random
import string
import inspect
from typing import Dict, Optional

from game.session import GameSession
from game.errors import (
    SessionNotFound,
    SessionAlreadyExists,
    PlayerAlreadyJoined,
    AlreadyInSession,
)


def generate_code(length: int = 6) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


class InMemoryStorage:
    """
    Storage for private-control model:
    - one active session per owner
    - join by code
    - quick lookup by player id
    """

    def __init__(self) -> None:
        self.by_code: Dict[str, GameSession] = {}
        self.by_owner: Dict[int, GameSession] = {}
        self.by_player: Dict[int, GameSession] = {}

    def _make_session(self, code: str, owner_id: int) -> GameSession:
        """
        Compatible constructor:
        Some versions of GameSession have chat_id, some don't.
        """
        sig = inspect.signature(GameSession)
        kwargs = {"code": code, "owner_id": owner_id}

        if "chat_id" in sig.parameters:
            kwargs["chat_id"] = 0  # not used in private model

        return GameSession(**kwargs)

    def create_session(self, owner_id: int) -> GameSession:
        if owner_id in self.by_owner:
            raise SessionAlreadyExists("Owner already has an active game.")

        code = generate_code()
        while code in self.by_code:
            code = generate_code()

        session = self._make_session(code=code, owner_id=owner_id)

        self.by_code[code] = session
        self.by_owner[owner_id] = session
        return session

    def get_by_code(self, code: str) -> GameSession:
        session = self.by_code.get(code.upper())
        if not session:
            raise SessionNotFound("Invalid code.")
        return session

    def get_session_for_player(self, telegram_id: int) -> Optional[GameSession]:
        return self.by_player.get(telegram_id)

    def join_by_code(self, code: str, telegram_id: int, username: Optional[str]) -> GameSession:
        session = self.get_by_code(code)

        # Already in some game
        if telegram_id in self.by_player:
            existing = self.by_player[telegram_id]
            if existing.code == session.code:
                raise PlayerAlreadyJoined("You are already in the lobby.")
            raise AlreadyInSession("You are already in a different game.")

        session.add_player(telegram_id, username)
        self.by_player[telegram_id] = session
        return session

    def end_session(self, code: str) -> None:
        session = self.by_code.get(code.upper())
        if not session:
            raise SessionNotFound("There is no active game.")

        # free players
        for p in list(session.players):
            self.by_player.pop(p.telegram_id, None)

        # free owner
        self.by_owner.pop(session.owner_id, None)

        # remove session
        self.by_code.pop(session.code, None)