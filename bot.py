import os
import asyncio
from dotenv import load_dotenv
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from storage.memory import InMemoryStorage
from game.errors import GameError

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not found. Check your .env file.")

storage = InMemoryStorage()


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 New game", callback_data="newgame")],
        [InlineKeyboardButton(text="👥 Players", callback_data="players")],
        [InlineKeyboardButton(text="🚀 Start", callback_data="start")],
        [InlineKeyboardButton(text="ℹ️ Status", callback_data="status")],
    ])


def is_group(chat: types.Chat) -> bool:
    return chat.type in ("group", "supergroup")


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def start_menu(message: types.Message):
        await message.answer("Control menu:", reply_markup=main_menu())

    @dp.message(Command("newgame"))
    async def newgame(message: types.Message):
        if not is_group(message.chat):
            await message.answer("This command works only in group chats.")
            return

        session = storage.create_session(message.chat.id, message.from_user.id)
        session.add_player(message.from_user.id, message.from_user.username)

        await message.answer(
            f"🎲 Game created!\n"
            f"Code: <b>{session.code}</b>\n"
            f"/join {session.code}\n"
            f"/players\n"
            f"/start"
        )

    @dp.message(Command("join"))
    async def join(message: types.Message):
        if not is_group(message.chat):
            return

        parts = message.text.split()
        if len(parts) != 2:
            await message.answer("Usage: /join CODE")
            return

        try:
            session = storage.get_by_code(parts[1])
            if session.chat_id != message.chat.id:
                await message.answer("This code belongs to another group chat.")
                return

            player = session.add_player(message.from_user.id, message.from_user.username)
            await message.answer(f"✅ {player.username} joined the lobby.")
        except GameError as e:
            await message.answer(f"⚠️ {e}")

    @dp.message(Command("players"))
    async def players(message: types.Message):
        try:
            session = storage.get_by_chat(message.chat.id)
            await message.answer(session.players_text())
        except GameError as e:
            await message.answer(f"⚠️ {e}")

    @dp.message(Command("start"))
    async def start(message: types.Message):
        try:
            session = storage.get_by_chat(message.chat.id)
            session.start(message.from_user.id)
            await message.answer("🚀 The game has started (M1).")
        except GameError as e:
            await message.answer(f"⚠️ {e}")

    @dp.callback_query()
    async def callbacks(call: types.CallbackQuery):
        data = call.data

        # Tell Telegram to remove the loading spinner on the button
        await call.answer()

        if data == "newgame":
            # Simulate /newgame
            message = call.message
            if not is_group(message.chat):
                await message.answer("This button works only in group chats.")
                return

            session = storage.create_session(message.chat.id, call.from_user.id)
            session.add_player(call.from_user.id, call.from_user.username)

            await message.answer(
                f"🎲 Game created!\n"
                f"Code: <b>{session.code}</b>\n"
                f"/join {session.code}\n"
                f"/players\n"
                f"/start",
                reply_markup=main_menu()
            )

        elif data == "players":
            message = call.message
            try:
                session = storage.get_by_chat(message.chat.id)
                await message.answer(session.players_text(), reply_markup=main_menu())
            except GameError as e:
                await message.answer(f"⚠️ {e}", reply_markup=main_menu())

        elif data == "start":
            message = call.message
            try:
                session = storage.get_by_chat(message.chat.id)
                session.start(call.from_user.id)
                await message.answer("🚀 The game has started (M1).", reply_markup=main_menu())
            except GameError as e:
                await message.answer(f"⚠️ {e}", reply_markup=main_menu())

        elif data == "status":
            message = call.message
            try:
                session = storage.get_by_chat(message.chat.id)
                await message.answer(
                    f"Status: <b>{session.state}</b>\n"
                    f"Code: <b>{session.code}</b>\n"
                    f"Players: {len(session.players)}/{session.max_players}",
                    reply_markup=main_menu()
                )
            except GameError as e:
                await message.answer(f"⚠️ {e}", reply_markup=main_menu())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
