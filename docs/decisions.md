# 📘 Aremes Bot – Technical Documentation

This document explains how the Aremes Telegram bot works internally.
It is written so you can understand every part of the project and easily modify it.

---

## 🧠 General Idea

The bot is a private-controlled deduction game.
No group chats are required.

All players interact with the bot in private messages.
The host creates a game and forwards an invite message to other players.

The bot avoids spam by:
- keeping only one panel message per user
- editing that message instead of sending new ones

---

## 🧩 Game Flow (High Level)

1. Host creates a game
2. Bot generates an invite message
3. Invite is forwarded to players
4. Players join via Join game button
5. Host starts the game
6. Bot sends cards to players privately

---

## 🏗 Project Architecture

The project is split into clear layers.

---

### 1️⃣ bot.py (Main Controller)

This is the main entry point.

Responsibilities:
- receives Telegram updates
- handles commands and buttons
- renders UI panels
- manages language switching
- coordinates storage and game logic

bot.py DOES NOT store game data permanently.

---

### 2️⃣ Storage Layer (storage/memory.py)

In-memory storage for active games.

Responsibilities:
- create new game sessions
- store sessions by invite code
- track which player is in which game
- end and clean up sessions

This layer contains NO Telegram code.

---

### 3️⃣ Game Logic (game/session.py)

Represents a single game session.

Responsibilities:
- store players
- check start conditions
- generate cards
- distribute cards
- track game state

This layer knows NOTHING about Telegram UI.

---

### 4️⃣ Errors (game/errors.py)

Custom exceptions used across the project.

Why?
- cleaner logic
- readable error handling
- easy localization of error messages

---

### 5️⃣ Localization (locales/*.json)

All user-facing text is stored in JSON files.

Why?
- easy translation
- no hardcoded text
- language switching without restarting the bot

Every message, button, and warning comes from JSON.

---

## 🌍 Language System

- language is stored per user
- default language is English
- user can change language at any time
- changing language re-renders UI instantly

Different users can use different languages at the same time.

---

## 🚫 Anti-Spam Design

The bot follows strict rules:
- no flooding chats
- no duplicate messages
- temporary warnings are auto-deleted
- main panel is always edited, not resent

This keeps chats clean and readable.

---

## 🔐 Invite System

Invite messages:
- contain a Join game button
- can be forwarded to any chat
- work via Telegram deep-links

When a user clicks Join game:
- the bot opens in private
- the user is joined automatically
- if already joined, the panel is simply shown again

---

## 🧪 Current Stage (M2)

Implemented:
- lobby system
- invite flow
- card generation
- private card distribution

Not yet implemented:
- turns
- accusations
- voting
- win conditions

---

## 🔮 Next Stage (M3)

Planned:
- turn-based gameplay
- making accusations
- checking accusations
- eliminating players
- detecting win conditions

---

## 🛠 How to Modify the Bot

- UI → edit bot.py rendering functions
- Game rules → edit game/session.py
- Texts → edit JSON in locales/
- Errors → edit game/errors.py

No database or migrations required.

---

This documentation is meant to help you fully understand the project and confidently change any part of it.