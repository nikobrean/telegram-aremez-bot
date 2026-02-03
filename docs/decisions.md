# Decisions (M1)

## Where state is stored
- Game state is stored in memory (Python objects) while the bot is running.
- If the bot restarts, all active sessions are lost.

## Session lifecycle
- Session states: LOBBY -> STARTED -> FINISHED.
- In M1 we implement only LOBBY and STARTED.

## Limits and rules
- 3–6 players per session.
- After STARTED, new players cannot join.
- Only the session owner (creator of /newgame) can run /start.

## Separation
- bot.py handles Telegram commands and messages.
- game logic (session rules and state transitions) is separate from Telegram handlers.
- Reason: keeps code readable and matches SOW non-functional requirement.
