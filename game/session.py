from dataclasses import dataclass, field
from enum import Enum

class GameState(str, Enum):
    LOBBY = "LOBBY"
    STARTED = "STARTED"

@dataclass
class Player:
    user_id: int
    username: str

@dataclass
class Session:
    chat_id: int
    owner_id: int
    max_players: int = 6
    state: GameState = GameState.LOBBY
    players: list[Player] = field(default_factory=list)

    panel_message_id: int | None = None
    lang: str = "ru"  # group language

    def is_owner(self, user_id: int) -> bool:
        return self.owner_id == user_id

    def add_player(self, user_id: int, username: str) -> str:
        if len(self.players) >= self.max_players:
            return "full"
        if any(p.user_id == user_id for p in self.players):
            return "exists"
        self.players.append(Player(user_id=user_id, username=username))
        return "ok"
