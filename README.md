# 🎲 Aremes Telegram Bot

Aremes is a Telegram game bot inspired by **deduction games**.
The goal is to understand **who did what, where, and with what**, using logic and accusations.

The bot is designed with:
- **Zero chat spam**
- **One interactive panel per user**
- **Private game control**
- **Multi-language support**

Even a child can understand how to start a game.

---

## 🌍 Languages

Supported languages:
- English (default)
- Русский
- עברית

Language affects:
- all texts
- buttons
- command descriptions
- notifications

Language can be changed **at any moment**.

---

## 🧩 Game Concept (MVP → M2)

- One player creates a game (host)
- Host sends an invite message to friends
- Friends join via **Join game** button
- Game starts when enough players joined
- Cards are sent **privately** to each player

No groups are required.

---

## ✨ Features

### Stage M1 (Lobby)
- Create a private lobby
- Invite players with one message
- Join via button
- Start game
- Refresh lobby
- Finish game
- No spam (panel is edited)

### Stage M2 (Current)
- Cards are generated
- Cards are sent in private messages
- Each player receives their own hand

---

## 🧠 How it works (simple)

### Private chat
1. Open the bot
2. Press **New game**
3. Forward invite message to friends
4. Friends press **Join game**
5. When ready, press **Start**

The bot always edits one panel message instead of sending many.

---

## 📜 Commands

### Private chat only
- `/start` — show main panel
- `/newgame` — create new game
- `/startgame` — start game (host)
- `/help` — help
- `/rules` — rules

---

## 🛠 Installation

### Requirements
- Python 3.10+
- aiogram v3
- python-dotenv

### Setup
```bash
git clone https://github.com/nikobrean/telegram-aremez-bot.git
cd telegram-aremez-bot
python -m venv .venv
