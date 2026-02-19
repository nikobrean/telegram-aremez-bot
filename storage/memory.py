from typing import Dict

from game.session import Session
from game.errors import SessionNotFound, SessionAlreadyExists


class InMemoryStorage:
    def __init__(self):
        self.by_chat: Dict[int, Session] = {}

    def create_session(self, chat_id: int, owner_id: int, lang: str = "en") -> Session:
        if chat_id in self.by_chat:
            raise SessionAlreadyExists()
        s = Session(chat_id=chat_id, owner_id=owner_id, lang=lang)
        self.by_chat[chat_id] = s
        return s

    def get_by_chat(self, chat_id: int) -> Session:
        s = self.by_chat.get(chat_id)
        if not s:
            raise SessionNotFound()
        return s

    def has_session(self, chat_id: int) -> bool:
        return chat_id in self.by_chat
