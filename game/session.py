from dataclasses import dataclass, field
from enum import Enum
from typing import Dict

from .errors import (
    PlayerAlreadyJoined,
    SessionFull,
    NotOwner,
    NotEnoughPlayers,
    SessionAlreadyStarted,
)


class GameState(str, Enum):
    LOBBY = "LOBBY"
    STARTED = "STARTED"


@dataclass
class Player:
    user_id: int
    name: str


@dataclass
class Session:
    chat_id: int
    owner_id: int
    lang: str = "en"
    max_players: int = 6
    state: GameState = GameState.LOBBY
    players: Dict[int, Player] = field(default_factory=dict)

    def add_player(self, user_id: int, name: str) -> None:
        if self.state == GameState.STARTED:
            raise SessionAlreadyStarted()
        if user_id in self.players:
            raise PlayerAlreadyJoined()
        if len(self.players) >= self.max_players:
            raise SessionFull()
        self.players[user_id] = Player(user_id=user_id, name=name)

    def start(self, user_id: int) -> None:
        if self.state == GameState.STARTED:
            raise SessionAlreadyStarted()
        if user_id != self.owner_id:
            raise NotOwner()
        if len(self.players) < 3:
            raise NotEnoughPlayers()
        self.state = GameState.STARTED
