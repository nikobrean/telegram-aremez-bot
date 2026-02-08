import os
import asyncio
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from storage.memory import InMemoryStorage
from game.errors import GameError

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not found. Check your .env file.")

# Your game sessions storage (in-memory)
game_storage = InMemoryStorage()

# FSM storage (temporary states like "waiting for join code")
fsm_storage = MemoryStorage()

# Fix for Hebrew (RTL) when showing LTR commands like "/join ABCD"
LRM = "\u200E"  # Left-to-Right Mark (invisible)

# Chat language (per group chat_id). Default = English.
chat_lang: dict[int, str] = {}  # chat_id -> "en" | "ru" | "he"


# -------------------------
# Translations dictionary
# -------------------------
TR = {
    "en": {
        "menu_title": "Control menu:",
        "btn_newgame": "🎲 New game",
        "btn_join": "➕ Join",
        "btn_players": "👥 Players",
        "btn_start": "🚀 Start",
        "btn_status": "ℹ️ Status",
        "btn_help": "❓ Help",
        "btn_languages": "🌐 Languages",
        "btn_back": "⬅️ Back",

        "only_group_cmd": "This command works only in group chats.",
        "join_only_group": "Join works only in group chats.",
        "send_join_code": "Send the join code (example: <code>{lrm}A1B2</code>).",

        "game_created": (
            "🎲 <b>Game created!</b>\n"
            "Code: <b>{code}</b>\n\n"
            "To join: <code>{lrm}/join {code}</code>\n"
            "Or press <b>Join</b> in the menu."
        ),
        "joined": "✅ {username} joined the lobby.",
        "code_other_group": "This code belongs to another group chat.",

        "status": "Status: <b>{state}</b>\nCode: <b>{code}</b>\nPlayers: {count}/{max}",
        "players_header": "Players ({count}/{max}):",

        "help": (
            "<b>How to use the bot</b>\n\n"
            "✅ <b>Create lobby</b>: <code>{lrm}/newgame</code> (group chat only)\n"
            "➕ <b>Join lobby</b>: <code>{lrm}/join CODE</code> (or press <b>Join</b>)\n"
            "👥 <b>Players</b>: <code>{lrm}/players</code>\n"
            "🚀 <b>Start</b>: <code>{lrm}/start</code> (owner only)\n\n"
            "<i>Tip:</i> Use the menu buttons to avoid typing commands."
        ),

        "lang_choose": "<b>Select language</b>:",
        "lang_set_en": "✅ Language set to English.",
        "lang_set_ru": "✅ Language set to Russian.",
        "lang_set_he": "✅ Language set to Hebrew.",

        "game_started": "🚀 The game has started (M1).",

        "err_SessionNotFound": "No active lobby. Use /newgame.",
        "err_PlayerAlreadyJoined": "You are already in the lobby.",
        "err_SessionAlreadyStarted": "The game has already started.",
        "err_SessionFull": "The lobby is full.",
        "err_NotEnoughPlayers": "Not enough players to start.",
        "err_NotOwner": "Only the lobby owner can start the game.",
        "err_default": "Something went wrong.",
    },

    "ru": {
        "menu_title": "Меню управления:",
        "btn_newgame": "🎲 Новая игра",
        "btn_join": "➕ Вступить",
        "btn_players": "👥 Игроки",
        "btn_start": "🚀 Старт",
        "btn_status": "ℹ️ Статус",
        "btn_help": "❓ Помощь",
        "btn_languages": "🌐 Язык",
        "btn_back": "⬅️ Назад",

        "only_group_cmd": "Эта команда работает только в группе.",
        "join_only_group": "Вступление работает только в группе.",
        "send_join_code": "Отправь код игры (пример: <code>{lrm}A1B2</code>).",

        "game_created": (
            "🎲 <b>Игра создана!</b>\n"
            "Код: <b>{code}</b>\n\n"
            "Чтобы вступить: <code>{lrm}/join {code}</code>\n"
            "Или нажми <b>Вступить</b> в меню."
        ),
        "joined": "✅ {username} присоединился к лобби.",
        "code_other_group": "Этот код относится к другой группе.",

        "status": "Статус: <b>{state}</b>\nКод: <b>{code}</b>\nИгроки: {count}/{max}",
        "players_header": "Игроки ({count}/{max}):",

        "help": (
            "<b>Как пользоваться ботом</b>\n\n"
            "✅ <b>Создать лобби</b>: <code>{lrm}/newgame</code> (только в группе)\n"
            "➕ <b>Вступить</b>: <code>{lrm}/join CODE</code> (или кнопка <b>Вступить</b>)\n"
            "👥 <b>Игроки</b>: <code>{lrm}/players</code>\n"
            "🚀 <b>Старт</b>: <code>{lrm}/start</code> (только создатель)\n\n"
            "<i>Совет:</i> используй кнопки меню, чтобы не вводить команды."
        ),

        "lang_choose": "<b>Выбери язык</b>:",
        "lang_set_en": "✅ Язык переключен на English.",
        "lang_set_ru": "✅ Язык переключен на Русский.",
        "lang_set_he": "✅ Язык переключен на עברית.",

        "game_started": "🚀 Игра началась (M1).",

        "err_SessionNotFound": "Нет активной игры. Используй /newgame.",
        "err_PlayerAlreadyJoined": "Ты уже в лобби.",
        "err_SessionAlreadyStarted": "Игра уже началась.",
        "err_SessionFull": "Лобби заполнено.",
        "err_NotEnoughPlayers": "Недостаточно игроков для старта.",
        "err_NotOwner": "Только создатель игры может начать.",
        "err_default": "Произошла ошибка.",
    },

    "he": {
        "menu_title": "תפריט שליטה:",
        "btn_newgame": "🎲 משחק חדש",
        "btn_join": "➕ הצטרפות",
        "btn_players": "👥 שחקנים",
        "btn_start": "🚀 התחלה",
        "btn_status": "ℹ️ סטטוס",
        "btn_help": "❓ עזרה",
        "btn_languages": "🌐 שפה",
        "btn_back": "⬅️ חזרה",

        "only_group_cmd": "הפקודה הזו עובדת רק בקבוצות.",
        "join_only_group": "הצטרפות עובדת רק בקבוצות.",
        "send_join_code": "שלח את קוד ההצטרפות (לדוגמה: <code>{lrm}A1B2</code>).",

        "game_created": (
            "🎲 <b>המשחק נוצר!</b>\n"
            "קוד: <b>{code}</b>\n\n"
            "כדי להצטרף: <code>{lrm}/join {code}</code>\n"
            "או לחץ <b>הצטרפות</b> בתפריט."
        ),
        "joined": "✅ {username} הצטרף ללובי.",
        "code_other_group": "הקוד הזה שייך לקבוצה אחרת.",

        "status": "סטטוס: <b>{state}</b>\nקוד: <b>{code}</b>\nשחקנים: {count}/{max}",
        "players_header": "שחקנים ({count}/{max}):",

        "help": (
            "<b>איך משתמשים בבוט</b>\n\n"
            "✅ <b>יצירת לובי</b>: <code>{lrm}/newgame</code> (רק בקבוצה)\n"
            "➕ <b>הצטרפות</b>: <code>{lrm}/join CODE</code> (או כפתור <b>הצטרפות</b>)\n"
            "👥 <b>שחקנים</b>: <code>{lrm}/players</code>\n"
            "🚀 <b>התחלה</b>: <code>{lrm}/start</code> (רק הבעלים)\n\n"
            "<i>טיפ:</i> השתמש בכפתורים כדי לא להקליד פקודות."
        ),

        "lang_choose": "<b>בחר שפה</b>:",
        "lang_set_en": "✅ השפה הוגדרה לאנגלית.",
        "lang_set_ru": "✅ השפה הוגדרה לרוסית.",
        "lang_set_he": "✅ השפה הוגדרה לעברית.",

        "game_started": "🚀 המשחק התחיל (M1).",

        "err_SessionNotFound": "אין לובי פעיל. השתמש ב־/newgame.",
        "err_PlayerAlreadyJoined": "אתה כבר בלובי.",
        "err_SessionAlreadyStarted": "המשחק כבר התחיל.",
        "err_SessionFull": "הלובי מלא.",
        "err_NotEnoughPlayers": "אין מספיק שחקנים כדי להתחיל.",
        "err_NotOwner": "רק בעל הלובי יכול להתחיל את המשחק.",
        "err_default": "משהו השתבש.",
    },
}


# -------------------------
# Helpers: language + text
# -------------------------
def get_lang(chat_id: int) -> str:
    return chat_lang.get(chat_id, "en")


def lrm_for(lang: str) -> str:
    # Apply LRM only for Hebrew (RTL). For EN/RU leave empty.
    return LRM if lang == "he" else ""


def t(lang: str, key: str, **kwargs) -> str:
    text = TR.get(lang, TR["en"]).get(key, TR["en"].get(key, key))
    # Always inject lrm (empty for EN/RU, LRM for HE)
    kwargs.setdefault("lrm", lrm_for(lang))
    return text.format(**kwargs) if kwargs else text


# -------------------------
# Keyboards
# -------------------------
def main_menu(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_newgame"), callback_data="newgame")],
        [InlineKeyboardButton(text=t(lang, "btn_join"), callback_data="join_flow")],
        [InlineKeyboardButton(text=t(lang, "btn_players"), callback_data="players")],
        [InlineKeyboardButton(text=t(lang, "btn_start"), callback_data="start")],
        [InlineKeyboardButton(text=t(lang, "btn_status"), callback_data="status")],
        [InlineKeyboardButton(text=t(lang, "btn_help"), callback_data="help")],
        [InlineKeyboardButton(text=t(lang, "btn_languages"), callback_data="languages")],
    ])


def back_menu(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="menu")]
    ])


def languages_menu(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="English", callback_data="lang:en"),
            InlineKeyboardButton(text="Русский", callback_data="lang:ru"),
            InlineKeyboardButton(text="עברית", callback_data="lang:he"),
        ],
        [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="menu")]
    ])


# -------------------------
# Misc helpers
# -------------------------
def is_group(chat: types.Chat) -> bool:
    return chat.type in ("group", "supergroup")


async def edit_menu_message(call: types.CallbackQuery, text: str, reply_markup: InlineKeyboardMarkup) -> None:
    """
    Edit the same message instead of sending a new one (prevents chat spam).
    """
    try:
        await call.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest:
        # Typical reason: "message is not modified"
        pass


def format_players(session, lang: str) -> str:
    lines = [t(lang, "players_header", count=len(session.players), max=session.max_players)]
    for i, p in enumerate(session.players, start=1):
        lines.append(f"{i}. {p.username}")
    return "\n".join(lines)


def translate_error(e: Exception, lang: str) -> str:
    """
    Translate game errors by class name.
    This works even if original exception messages are in Russian.
    """
    name = type(e).__name__
    key = f"err_{name}"
    if key in TR.get(lang, {}):
        return t(lang, key)
    if key in TR["en"]:
        return TR["en"][key]
    return t(lang, "err_default")


# -------------------------
# Join flow (FSM)
# -------------------------
class JoinFlow(StatesGroup):
    waiting_for_code = State()


# -------------------------
# Main
# -------------------------
async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=fsm_storage)

    @dp.message(CommandStart())
    async def start_menu(message: types.Message):
        lang = get_lang(message.chat.id)
        await message.answer(t(lang, "menu_title"), reply_markup=main_menu(lang))

    @dp.message(Command("help"))
    async def help_cmd(message: types.Message):
        lang = get_lang(message.chat.id)
        await message.answer(t(lang, "help"))

    @dp.message(Command("newgame"))
    async def newgame(message: types.Message):
        lang = get_lang(message.chat.id)

        if not is_group(message.chat):
            await message.answer(t(lang, "only_group_cmd"))
            return

        session = game_storage.create_session(message.chat.id, message.from_user.id)
        session.add_player(message.from_user.id, message.from_user.username)

        await message.answer(t(lang, "game_created", code=session.code), reply_markup=main_menu(lang))

    @dp.message(Command("join"))
    async def join_command(message: types.Message, state: FSMContext):
        lang = get_lang(message.chat.id)

        if not is_group(message.chat):
            await message.answer(t(lang, "join_only_group"))
            return

        parts = (message.text or "").split(maxsplit=1)
        if len(parts) == 2:
            await do_join(message, parts[1].strip(), lang)
            return

        await state.set_state(JoinFlow.waiting_for_code)
        await message.answer(t(lang, "send_join_code"))

    @dp.message(JoinFlow.waiting_for_code)
    async def join_flow_receive_code(message: types.Message, state: FSMContext):
        lang = get_lang(message.chat.id)

        if not is_group(message.chat):
            await state.clear()
            return

        code = (message.text or "").strip()
        if not code:
            await message.answer(t(lang, "send_join_code"))
            return

        await do_join(message, code, lang)

        # Optional: remove the code message to reduce spam (works if bot is admin)
        try:
            await message.delete()
        except Exception:
            pass

        await state.clear()

    @dp.message(Command("players"))
    async def players_cmd(message: types.Message):
        lang = get_lang(message.chat.id)
        try:
            session = game_storage.get_by_chat(message.chat.id)
            await message.answer(format_players(session, lang))
        except GameError as e:
            await message.answer(f"⚠️ {translate_error(e, lang)}")

    @dp.message(Command("start"))
    async def start_cmd(message: types.Message):
        lang = get_lang(message.chat.id)
        try:
            session = game_storage.get_by_chat(message.chat.id)
            session.start(message.from_user.id)
            await message.answer(t(lang, "game_started"))
        except GameError as e:
            await message.answer(f"⚠️ {translate_error(e, lang)}")

    @dp.callback_query()
    async def callbacks(call: types.CallbackQuery, state: FSMContext):
        chat_id = call.message.chat.id
        lang = get_lang(chat_id)
        data = call.data or ""

        await call.answer()  # remove loading spinner

        if data == "menu":
            await state.clear()
            lang = get_lang(chat_id)
            await edit_menu_message(call, t(lang, "menu_title"), main_menu(lang))
            return

        if data == "help":
            await edit_menu_message(call, t(lang, "help"), back_menu(lang))
            return

        if data == "languages":
            await edit_menu_message(call, t(lang, "lang_choose"), languages_menu(lang))
            return

        if data.startswith("lang:"):
            new_lang = data.split(":", 1)[1]
            if new_lang not in ("en", "ru", "he"):
                new_lang = "en"

            chat_lang[chat_id] = new_lang
            await state.clear()

            # Show confirmation in the selected language
            await edit_menu_message(call, t(new_lang, f"lang_set_{new_lang}"), main_menu(new_lang))
            return

        if data == "join_flow":
            if not is_group(call.message.chat):
                await edit_menu_message(call, t(lang, "join_only_group"), back_menu(lang))
                return
            await state.set_state(JoinFlow.waiting_for_code)
            await edit_menu_message(call, t(lang, "send_join_code"), back_menu(lang))
            return

        if data == "newgame":
            if not is_group(call.message.chat):
                await edit_menu_message(call, t(lang, "only_group_cmd"), back_menu(lang))
                return

            session = game_storage.create_session(chat_id, call.from_user.id)
            session.add_player(call.from_user.id, call.from_user.username)

            await edit_menu_message(call, t(lang, "game_created", code=session.code), back_menu(lang))
            return

        if data == "players":
            try:
                session = game_storage.get_by_chat(chat_id)
                await edit_menu_message(call, format_players(session, lang), back_menu(lang))
            except GameError as e:
                await edit_menu_message(call, f"⚠️ {translate_error(e, lang)}", back_menu(lang))
            return

        if data == "start":
            try:
                session = game_storage.get_by_chat(chat_id)
                session.start(call.from_user.id)
                await edit_menu_message(call, t(lang, "game_started"), back_menu(lang))
            except GameError as e:
                await edit_menu_message(call, f"⚠️ {translate_error(e, lang)}", back_menu(lang))
            return

        if data == "status":
            try:
                session = game_storage.get_by_chat(chat_id)
                await edit_menu_message(
                    call,
                    t(lang, "status",
                      state=str(session.state),
                      code=session.code,
                      count=len(session.players),
                      max=session.max_players),
                    back_menu(lang),
                )
            except GameError as e:
                await edit_menu_message(call, f"⚠️ {translate_error(e, lang)}", back_menu(lang))
            return

    async def do_join(message: types.Message, code: str, lang: str) -> None:
        try:
            session = game_storage.get_by_code(code)
            if session.chat_id != message.chat.id:
                await message.answer(t(lang, "code_other_group"))
                return

            player = session.add_player(message.from_user.id, message.from_user.username)
            await message.answer(t(lang, "joined", username=player.username))
        except GameError as e:
            await message.answer(f"⚠️ {translate_error(e, lang)}")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
