from game.session import Session

class InMemoryStorage:
    def __init__(self):
        self.by_chat: dict[int, Session] = {}

    def create(self, chat_id: int, owner_id: int) -> Session:
        s = Session(chat_id=chat_id, owner_id=owner_id)
        self.by_chat[chat_id] = s
        return s

    def get(self, chat_id: int) -> Session | None:
        return self.by_chat.get(chat_id)
