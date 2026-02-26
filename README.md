# 🎲 Aremes Telegram Bot

Aremes is a Telegram game bot inspired by deduction games.
The goal of the game is to understand who did what, where, and with what, using logic and accusations.

The bot is designed with:
- Zero chat spam
- One interactive panel per user
- Private game control
- Full multi-language support

The interface is intentionally simple so that even a child can understand how to start a game.

---

## 🌍 Languages

Supported languages:
- English (default)
- Русский
- עברית

Language selection affects:
- all texts in the bot
- button labels
- command descriptions in Telegram
- notifications and warnings

Language can be changed at any time.

---

## 🧩 Game Concept

- One player creates a game (host)
- The host sends an invite message to friends
- Friends join the game via the Join game button
- When enough players joined, the host starts the game
- Cards are sent privately to each player

No groups are required. The entire game is controlled via private chats.

---

## ✨ Features

M1 — Lobby
- Create a private game lobby
- Invite players with a single message
- Join game via button
- Refresh lobby
- Start game (host only)
- Finish game (host only)
- Zero spam (one message is edited instead of sending many)

M2 — Cards (current stage)
- Cards are generated automatically
- Cards are distributed privately to players
- Each player sees only their own cards

---

## 🧠 How the Bot Works (Simple Explanation)

Private Chat Flow:
1. Open the bot
2. Press New game
3. Forward the invite message to friends
4. Friends press Join game
5. When ready, press Start

The bot always keeps one panel message and edits it instead of sending new messages.

---

## 📜 Commands

Private chat only:
- /start — show main panel
- /newgame — create a new game
- /startgame — start the game (host only)
- /help — how to play
- /rules — game rules

---

## 🛠 Installation

Requirements:
- Python 3.10+
- aiogram v3
- python-dotenv

Setup:
1. Clone the repository
   git clone https://github.com/nikobrean/telegram-aremez-bot.git
   cd telegram-aremez-bot

2. Create virtual environment
   python -m venv .venv

3. Activate virtual environment
   Windows:
   .venv\\Scripts\\activate

   Mac / Linux:
   source .venv/bin/activate

4. Install dependencies
   pip install aiogram python-dotenv

5. Create .env file in project root
   BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN

6. Run the bot
   python bot.py

If everything is correct, you will see:
✅ Bot is running: @YourBotName (id=...)

---

## 📁 Project Structure

bot.py
storage/
  memory.py
game/
  session.py
  errors.py
locales/
  en.json
  ru.json
  he.json
docs/
  OVERVIEW.md

---

## 🚀 Project Status

- M1 (Lobby): Completed
- M2 (Cards): Completed
- M3 (Turns & Accusations): Planned

---

## ⚠️ Important Notes

- The bot works only in private chats
- Invite messages can be forwarded freely
- Cards are NEVER shown publicly
- All user-facing text is stored in JSON files
- No database is used (in-memory MVP design)

---

Made with love for logic and deduction games.
