# Aremes Bot — Architecture & Logic (Stage 1)

This document explains **how the Aremes Telegram bot works internally**,  
why certain UX decisions were made, and how the lobby system is designed.

This is **Stage 1 (Lobby MVP)**.

---

## 🎯 Main goal

Create a Telegram game bot that:
- does NOT spam the chat
- is easy to understand even for a child
- works equally well in groups and private chats
- supports multiple languages
- can be extended later into a full game

---

## 🧱 Core design principles

### 1. One message — zero spam
The bot always keeps **one main panel message** in each chat.

Instead of sending new messages, the bot:
- edits the existing panel
- updates buttons and text dynamically

This keeps the chat clean and readable.

---

### 2. Everything through buttons
Most interactions are done via **inline buttons**, not text commands.

Commands exist mainly for:
- `/start`
- `/newgame`
- `/startgame`
- `/help`
- `/rules`

But the recommended way is using buttons.

---

### 3. Simple UX (child-friendly)
Every screen answers one question only:
- What is happening?
- What should I press next?

No technical language, no hidden actions.

---

## 🌍 Language system (i18n)

### How languages work
- All texts are stored in `locales/*.json`
- The code never contains hardcoded text
- Language can be changed at any moment

There are two independent language scopes:
- **Group language** (per chat)
- **Private language** (per user)

---

### Telegram command menu language
Telegram normally ties command descriptions to the Telegram app language.

This bot **overrides that behavior**:
- When a user changes language inside the bot
- Command descriptions are updated for **all Telegram language codes**
- This guarantees consistency between bot UI and command descriptions

---

## 🧩 Project structure

```text
bot.py                 Main bot entry point
locales/               All translations (JSON)
game/
  session.py           Game session & state logic
  errors.py            Custom game exceptions
storage/
  memory.py            In-memory session storage
docs/
  ARCHITECTURE.md      This document
```

---

## 🎲 Lobby system (Stage 1)

### Lobby lifecycle
1. No game exists → group shows **Home panel**
2. Host presses **New game**
3. Lobby is created
4. Players press **Join**
5. When there are 3–6 players → host presses **Start**

---

### Lobby rules
- Minimum players: **3**
- Maximum players: **6**
- Only the host can start the game
- A player cannot join twice
- The lobby cannot be created twice in the same chat

All violations are handled via **controlled errors**, not crashes.

---

## 🔄 Refresh button — why it exists

The **Refresh** button does NOT affect the game logic.

It only:
- re-renders the lobby screen
- helps if Telegram failed to update the message automatically

The button is optional and safe to ignore if the screen looks correct.

---

## 🚫 No modal popups
The bot intentionally avoids:
- blocking alerts
- modal confirmation windows
- “OK” dialogs

Instead, it uses:
- top notifications (toast-style)
- silent panel updates

This keeps the experience smooth and fast.

---

## 🔐 Storage model

Stage 1 uses **in-memory storage**:
- All sessions are stored in RAM
- If the bot restarts, sessions are lost

This is intentional for MVP simplicity.

Persistent storage (DB) can be added later.

---

## 🚀 Future stages (planned)

- Stage 2: Full game logic
- Stage 3: Roles & turns
- Stage 4: Persistence (database)
- Stage 5: Anti-cheat & moderation tools

Stage 1 is designed to support all future stages without rewriting the core.

---

## ✅ Summary

Stage 1 focuses on:
- UX clarity
- clean chats
- simple logic
- extensible architecture

Everything else builds on top of this foundation.
