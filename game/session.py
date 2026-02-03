from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

from .player import Player
from .errors import (
    PlayerAlreadyJoined,
    SessionAlreadyStarted,
    SessionFull,
    NotEnoughPlayers,
    NotOwner,
)


class SessionState(str, Enum):
    LOBBY = "LOBBY"
    STARTED = "STARTED"
    FINISHED = "FINISHED"


def normalize_username(username: Optional[str], user_id: int) -> str:
    if username and username.strip():
        return "@" + username.lstrip("@")
    return f"user_{user_id}"


@dataclass
class GameSession:
    code: str
    chat_id: int
    owner_id: int
    created_at: datetime = field(default_factory=datetime.utcnow)

    state: SessionState = SessionState.LOBBY
    players: List[Player] = field(default_factory=list)

    min_players: int = 3
    max_players: int = 6

    def add_player(self, telegram_id: int, username: Optional[str]) -> Player:
        if self.state != SessionState.LOBBY:
            raise SessionAlreadyStarted("Игра уже началась. Присоединиться нельзя.")

        if any(p.telegram_id == telegram_id for p in self.players):
            raise PlayerAlreadyJoined("Ты уже в игре.")

        if len(self.players) >= self.max_players:
            raise SessionFull(f"Игра заполнена (макс {self.max_players}).")

        player = Player(
            telegram_id=telegram_id,
            username=normalize_username(username, telegram_id),
            joined_at=datetime.utcnow(),
        )
        self.players.append(player)
        return player

    def start(self, requester_id: int) -> None:
        if requester_id != self.owner_id:
            raise NotOwner("Только создатель игры может её начать.")

        if self.state != SessionState.LOBBY:
            raise SessionAlreadyStarted("Игра уже началась.")

        if len(self.players) < self.min_players:
            raise NotEnoughPlayers(f"Нужно минимум {self.min_players} игроков.")

        self.state = SessionState.STARTED

    def players_text(self) -> str:
        lines = [f"Игроки ({len(self.players)}/{self.max_players}):"]
        for i, p in enumerate(self.players, start=1):
            lines.append(f"{i}. {p.username}")
        return "\n".join(lines)
