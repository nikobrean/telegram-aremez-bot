# Telegram Clue Bot

Telegram bot for a multiplayer Clue-style game.  
Built as an educational project in Python.

This project is developed step by step with a focus on clean architecture,
game logic separation, and responsible use of AI tools.

---

## Project Status

- Current milestone: **M1 — Lobby & Sessions**
- Status: **In progress / stable for M1**
- Platform: Telegram groups

At this stage, the project focuses on creating and managing game lobbies.
Full game mechanics will be implemented in later milestones.

---

## Features (M1)

- Create a new game lobby
- Generate and share a join code
- Join a lobby using the join code
- List players in the lobby
- Basic session validation and error handling
- In-memory session storage

---

## Planned Features

- Card dealing and Case File generation
- Private player hands via direct messages (DM)
- Suggest and Accuse actions
- Full Classic Mode game flow
- Improved UX with inline buttons
- Optional persistence (SQLite) in later versions

---

## Tech Stack

- **Python 3**
- **aiogram 3.x**
- **asyncio**
- Telegram Bot API

---

## Project Structure

```text
bot.py        - Telegram bot entrypoint (handlers, routers, startup)
game/         - Game domain logic (sessions, rules, errors)
storage/      - In-memory storage for game sessions
docs/         - Project documentation and design decisions
```
## How to Run Locally

1. Clone the repository  
2. Create a `.env` file in the project root  
3. Add your Telegram bot token to `.env`:

```env
BOT_TOKEN=your_bot_token_here
```
4. Install dependencies
5. Run the bot:
```
python bot.py
```


## Notes
- The .env file is ignored by git and must not be committed

- In M1, all game state is stored in memory and will be lost on restart

- This project is intended as a learning and portfolio project