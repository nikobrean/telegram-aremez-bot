# Decisions (M1)

This document records key technical decisions for version 1.0 (Classic Mode), milestone M1 (Lobby & Sessions).

## 1. Telegram framework
**Decision:** Use `aiogram 3.x` (async) for the bot.
**Why:** Modern Telegram bot framework, good async support, convenient routers/handlers.
**Alternative:** python-telegram-bot. Chosen aiogram because the project already started with it and it fits async design.

## 2. Project structure
**Decision:** Separate Telegram/UI layer from game logic and storage.

- `bot.py` — Telegram entrypoint: dispatcher, routers, handlers, keyboards.
- `game/` — game domain objects and rules (session, player, errors).
- `storage/` — session storage implementation (in-memory for M1).
- `docs/` — documentation (this file + later architecture and rules).

**Why:** Makes code easier to test and reason about. Game rules can be developed independently from Telegram.

## 3. Public vs private data (future requirement)
**Decision:** In Classic Mode, all public actions happen in group chat, private data must go to DM.
**Current status:** In M1 we only implement lobby/session management. Private card DM logic is part of M2+.
**Why:** Telegram group messages are visible to everyone, so private info must never be posted in the group.

## 4. State model (session)
**Decision:** Use a `Session` as the main state object per game lobby.
Session includes:
- chat_id (group chat identifier)
- join_code
- list of players
- status (lobby / started / finished) — in M1 mainly lobby

**Why:** It matches how the game works: one group chat = one game instance.

## 5. Storage
**Decision:** Use in-memory storage in M1 (dictionary in `storage/memory.py`).
**Why:** Fast to implement, enough for learning and M1 requirements.
**Trade-off:** If the bot restarts, sessions disappear.
**Future:** Consider SQLite persistence in v2 (optional in SOW).

## 6. Error handling
**Decision:** Use custom exceptions for rule violations (e.g. "game not found", "already started", "not enough players").
Handlers catch these exceptions and send a friendly message to the user.

**Why:** Keeps rule checks inside `game/` and keeps Telegram handlers clean.

## 7. UX: commands first, buttons later
**Decision:** M1 supports commands for core actions. Inline buttons will be added as UX improvement after M1 is stable.
**Why:** Commands are simplest and fastest to debug. Buttons require callbacks and more UI work.

## 8. Security / secrets
**Decision:** Store `BOT_TOKEN` in `.env` and never commit it to GitHub.
**How:** `.env` is included in `.gitignore`.
**Why:** Token gives full control over the bot, must not leak.

## 9. Logging
**Decision:** Print basic startup/log messages to console during development.
**Why:** Helps debugging. Logs must never contain secrets.

## 10. What is done in M1
- Create a new lobby
- Join with code
- List players
- Start session (basic state change)
- Basic validation/errors

## 11. Next milestone (M2) preview
- Create Case File (Suspect + Location + Item)
- Shuffle + deal cards
- DM `/hand` and enforce privacy
- No duplicate cards, case file cards not in hands
