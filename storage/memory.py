import random
import string
from typing import Dict

from game.session import GameSession
from game.errors import SessionNotFound, SessionAlreadyExists


def generate_code(length: int = 4) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


class InMemoryStorage:
    def __init__(self) -> None:
        self.by_chat: Dict[int, GameSession] = {}
        self.by_code: Dict[str, GameSession] = {}

    def has_session(self, chat_id: int) -> bool:
        return chat_id in self.by_chat

    def create_session(self, chat_id: int, owner_id: int) -> GameSession:
        if chat_id in self.by_chat:
            raise SessionAlreadyExists("This chat already has an active game.")

        code = generate_code()
        while code in self.by_code:
            code = generate_code()

        session = GameSession(code=code, chat_id=chat_id, owner_id=owner_id)
        self.by_chat[chat_id] = session
        self.by_code[code] = session
        return session

    def get_by_chat(self, chat_id: int) -> GameSession:
        session = self.by_chat.get(chat_id)
        if not session:
            raise SessionNotFound("There is no active game. Use /newgame")
        return session

    def get_by_code(self, code: str) -> GameSession:
        session = self.by_code.get(code.upper())
        if not session:
            raise SessionNotFound("Invalid code.")
        return session

    def delete_session(self, chat_id: int) -> None:
        session = self.by_chat.get(chat_id)
        if not session:
            raise SessionNotFound("There is no active game.")
        self.by_chat.pop(chat_id, None)
        self.by_code.pop(session.code, None)