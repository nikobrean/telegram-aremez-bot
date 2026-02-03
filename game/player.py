from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Player:
    telegram_id: int
    username: str
    joined_at: datetime
