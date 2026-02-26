from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import random

from .player import Player
from .errors import PlayerAlreadyJoined, SessionFull, NotEnoughPlayers, NotOwner, SessionAlreadyStarted


def default_cards() -> Tuple[List[str], List[str], List[str]]:
    # Заглушки — потом заменишь на реальные
    characters = [f"character_{i}" for i in range(1, 7)]   # 6
    weapons = [f"weapon_{i}" for i in range(1, 7)]         # 6
    locations = [f"location_{i}" for i in range(1, 10)]    # 9
    return characters, weapons, locations


def normalize_username(username: Optional[str], user_id: int) -> str:
    if username and username.strip():
        return "@" + username.lstrip("@")
    return f"user_{user_id}"


@dataclass
class GameSession:
    code: str
    owner_id: int
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Lobby rules
    min_players: int = 3
    max_players: int = 6

    players: List[Player] = field(default_factory=list)
    started: bool = False

    # M2: solution + hands
    solution_character: Optional[str] = None
    solution_weapon: Optional[str] = None
    solution_location: Optional[str] = None
    hands: Dict[int, List[str]] = field(default_factory=dict)

    # Card pools
    characters: List[str] = field(default_factory=list)
    weapons: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)

    def ensure_cards_loaded(self) -> None:
        if not self.characters and not self.weapons and not self.locations:
            c, w, l = default_cards()
            self.characters = c
            self.weapons = w
            self.locations = l

    def add_player(self, telegram_id: int, username: Optional[str]) -> None:
        if self.started:
            raise SessionAlreadyStarted("Game has already started.")

        if any(p.telegram_id == telegram_id for p in self.players):
            raise PlayerAlreadyJoined("Already joined.")

        if len(self.players) >= self.max_players:
            raise SessionFull("Lobby is full.")

        self.players.append(Player(
            telegram_id=telegram_id,
            username=normalize_username(username, telegram_id),
            joined_at=datetime.utcnow(),
        ))

    def deal_cards(self) -> None:
        self.ensure_cards_loaded()

        self.solution_character = random.choice(self.characters)
        self.solution_weapon = random.choice(self.weapons)
        self.solution_location = random.choice(self.locations)

        deck = (
            [c for c in self.characters if c != self.solution_character]
            + [w for w in self.weapons if w != self.solution_weapon]
            + [l for l in self.locations if l != self.solution_location]
        )
        random.shuffle(deck)

        self.hands = {p.telegram_id: [] for p in self.players}
        if not self.players:
            return

        i = 0
        for card in deck:
            pid = self.players[i % len(self.players)].telegram_id
            self.hands[pid].append(card)
            i += 1

    def start(self, requester_id: int) -> None:
        if requester_id != self.owner_id:
            raise NotOwner("Only owner can start.")
        if self.started:
            raise SessionAlreadyStarted("Already started.")
        if len(self.players) < self.min_players:
            raise NotEnoughPlayers("Not enough players.")
        self.deal_cards()
        self.started = True