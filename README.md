# Aremes Telegram Bot (Lobby MVP)

Aremes is a Telegram game bot designed with **maximum simplicity** and **zero chat spam**.  
The bot always keeps **one main panel message** in the chat and **edits it instead of sending new messages**.

The interface is intentionally simple so that **even a child can understand how to play**.

---

## 🌍 Languages

The bot supports **three languages**:

- English (default)
- Русский
- עברית

The selected language:
- changes **all texts in the bot**
- changes **button labels**
- changes **Telegram command descriptions**
- can be changed **at any time**, both in private chats and in groups

---

## ✨ Features (Stage 1 / MVP)

- 🎲 Create a game lobby in a group chat
- ✅ Players can join the lobby
- ▶️ Host can start the game
- 👥 Minimum **3**, maximum **6** players
- 🔄 Refresh button (only updates the screen)
- 🌐 Language switch at any moment
- ❓ Commands list inside the bot
- 📜 Rules screen
- 🚫 No spam: only one message is edited

---

## 🔄 Refresh button (important)

The **Refresh** button does **NOT** restart the game.

It only:
- updates the lobby screen
- re-draws the list of players
- helps if Telegram did not refresh the message automatically

If everything looks correct, **you do not need to press Refresh**.

---

## 🤖 How the bot works (simple explanation)

### In a group chat

1. Add the bot to a group  
2. Send `/start`  
3. Press **🎲 New game**  
4. Players press **✅ Join**  
5. When there are **3–6 players**, the host presses **▶️ Start**

The bot edits the same message instead of sending new ones.

---

### In a private chat

- `/start` shows instructions
- Only two buttons are available:
  - 📜 Rules
  - 🌐 Language

No game actions are available in private chat.

---

## 🧠 Commands

### Group chats
- `/start` — show main panel  
- `/newgame` — create a lobby  
- `/startgame` — start the game (host only)  
- `/help` — how to play  
- `/rules` — game rules  

### Private chat
- `/start` — instructions  
- `/help` — help  
- `/rules` — rules  

---

## 🛠 Installation

### Requirements
- Python **3.10+**
- **aiogram v3**
- **python-dotenv**

---

### 1. Clone the repository
```bash
git clone https://github.com/nikobrean/telegram-aremez-bot.git
cd telegram-aremez-bot
```

---

### 2. Create virtual environment (recommended)
```bash
python -m venv .venv
```

**Windows**
```bash
.venv\Scripts\activate
```

**Mac / Linux**
```bash
source .venv/bin/activate
```

---

### 3. Install dependencies
```bash
pip install aiogram python-dotenv
```

---

### 4. Create `.env` file

Create a file named `.env` in the project root:

```env
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
```

⚠️ **Never upload `.env` to GitHub.**

---

### 5. Run the bot
```bash
python bot.py
```

If everything is correct, you will see:

```text
✅ Bot is running: @YourBotName (id=...)
```

---

## 📁 Project structure

```text
bot.py
.env                (ignored by git)
locales/
  en.json
  ru.json
  he.json
game/
  session.py
  errors.py
storage/
  memory.py
```

---

## 🚀 GitHub upload (quick)

```bash
git add .
git commit -m "Update bot logic and translations"
git push
```

---

## 📝 Notes

- This repository contains **Stage 1 (Lobby MVP)** only  
- Full game logic will be added later  
- All texts and explanations are handled via **JSON localization files**  
- The bot is designed to be **simple, clean, and non-intrusive**
