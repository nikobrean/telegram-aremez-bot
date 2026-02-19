import os
import json
import asyncio
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties/

from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from aiogram.types import BotCommand
from aiogram.types import (
    BotCommandScopeDefault,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeAllGroupChats,
)

from storage.memory import InMemoryStorage
from game.errors import (
    GameError,
    SessionNotFound,
    SessionAlreadyExists,
    PlayerAlreadyJoined,
    SessionFull,
    NotOwner,
    NotEnoughPlayers,
    SessionAlreadyStarted,
)
from game.session import GameState

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not found in .env")

DEFAULT_LANG = "en"
SUPPORTED_LANGS = ("en", "ru", "he")

storage = InMemoryStorage()

# one panel message per group chat and per private user
GROUP_PANEL_ID: Dict[int, int] = {}
PRIVATE_PANEL_ID: Dict[int, int] = {}

# language storage
CHAT_LANG: Dict[int, str] = {}
USER_LANG: Dict[int, str] = {}


# ---------- i18n ----------
def load_tr() -> Dict[str, Dict[str, str]]:
    base = Path(__file__).parent / "locales"
    out: Dict[str, Dict[str, str]] = {}
    for lang in SUPPORTED_LANGS:
        p = base / f"{lang}.json"
        if not p.exists():
            raise RuntimeError(f"Missing locales file: {p}")
        out[lang] = json.loads(p.read_text(encoding="utf-8"))
    return out


TR = load_tr()


def t(lang: str, key: str, **kwargs) -> str:
    lang = lang if lang in TR else DEFAULT_LANG
    txt = TR[lang].get(key) or TR[DEFAULT_LANG].get(key) or key
    return txt.format(**kwargs) if kwargs else txt


def is_group(chat: types.Chat) -> bool:
    return chat.type in ("group", "supergroup")


def safe_name(u: types.User) -> str:
    return f"@{u.username}" if u.username else u.full_name


def get_chat_lang(chat_id: int) -> str:
    return CHAT_LANG.get(chat_id, DEFAULT_LANG)


def set_chat_lang(chat_id: int, lang: str) -> str:
    lang = lang if lang in SUPPORTED_LANGS else DEFAULT_LANG
    CHAT_LANG[chat_id] = lang
    return lang


def get_user_lang(uid: int) -> str:
    return USER_LANG.get(uid, DEFAULT_LANG)


def set_user_lang(uid: int, lang: str) -> str:
    lang = lang if lang in SUPPORTED_LANGS else DEFAULT_LANG
    USER_LANG[uid] = lang
    return lang


async def safe_edit(bot: Bot, chat_id: int, message_id: int, text: str, kb: InlineKeyboardMarkup) -> None:
    try:
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=kb)
    except TelegramBadRequest:
        # includes "message is not modified"
        pass


async def try_delete(msg: types.Message) -> None:
    try:
        await msg.delete()
    except Exception:
        pass


async def toast(call: types.CallbackQuery, text: str) -> None:
    # top notification (not blocking)
    try:
        await call.answer(text, show_alert=False)
    except Exception:
        pass


# ---------- Telegram Menu commands (NO /players) ----------
def build_commands_group(lang: str):
    return [
        BotCommand(command="start", description=t(lang, "cmd_start_desc")),
        BotCommand(command="newgame", description=t(lang, "cmd_newgame_desc")),
        BotCommand(command="startgame", description=t(lang, "cmd_startgame_desc")),
        BotCommand(command="help", description=t(lang, "cmd_help_desc")),
        BotCommand(command="rules", description=t(lang, "cmd_rules_desc")),
    ]


def build_commands_private(lang: str):
    return [
        BotCommand(command="start", description=t(lang, "cmd_start_desc")),
        BotCommand(command="help", description=t(lang, "cmd_help_desc")),
        BotCommand(command="rules", description=t(lang, "cmd_rules_desc")),
    ]


async def apply_telegram_commands(bot: Bot, chosen_lang: str):
    """
    Telegram Menu follows language chosen INSIDE the bot, not Telegram app language:
    set for en/ru/he all the same chosen language.
    """
    chosen_lang = chosen_lang if chosen_lang in SUPPORTED_LANGS else DEFAULT_LANG

    for lc in SUPPORTED_LANGS:
        await bot.set_my_commands(
            build_commands_private(chosen_lang),
            scope=BotCommandScopeAllPrivateChats(),
            language_code=lc,
        )
        await bot.set_my_commands(
            build_commands_group(chosen_lang),
            scope=BotCommandScopeAllGroupChats(),
            language_code=lc,
        )

    # default fallback: minimal
    await bot.set_my_commands(
        build_commands_private(chosen_lang),
        scope=BotCommandScopeDefault(),
        language_code=None,
    )


# ---------- Keyboards ----------
def kb_group_home(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_newgame"), callback_data="home:newgame")],
        [
            InlineKeyboardButton(text=t(lang, "btn_language"), callback_data="menu:group:lang"),
            InlineKeyboardButton(text=t(lang, "btn_commands"), callback_data="menu:group:commands"),
        ],
        [InlineKeyboardButton(text=t(lang, "btn_rules"), callback_data="menu:group:rules")],
    ])


def kb_group_lobby(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t(lang, "btn_join"), callback_data="lobby:join"),
            InlineKeyboardButton(text=t(lang, "btn_start"), callback_data="lobby:start"),
        ],
        [
            InlineKeyboardButton(text=t(lang, "btn_refresh"), callback_data="lobby:refresh"),
            InlineKeyboardButton(text=t(lang, "btn_language"), callback_data="menu:group:lang"),
        ],
        [
            InlineKeyboardButton(text=t(lang, "btn_commands"), callback_data="menu:group:commands"),
            InlineKeyboardButton(text=t(lang, "btn_rules"), callback_data="menu:group:rules"),
        ],
    ])


def kb_private_menu(lang: str) -> InlineKeyboardMarkup:
    # ONLY 2 buttons in private: Rules + Language
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_rules"), callback_data="menu:pm:rules")],
        [InlineKeyboardButton(text=t(lang, "btn_language"), callback_data="menu:pm:lang")],
    ])


def kb_lang(lang: str, scope: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="English", callback_data=f"lang:{scope}:en"),
            InlineKeyboardButton(text="Русский", callback_data=f"lang:{scope}:ru"),
            InlineKeyboardButton(text="עברית", callback_data=f"lang:{scope}:he"),
        ],
        [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data=f"back:{scope}")],
    ])


def kb_back(lang: str, scope: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data=f"back:{scope}")]
    ])


# ---------- Panel rendering ----------
def render_group_home(chat_id: int) -> str:
    lang = get_chat_lang(chat_id)
    return t(lang, "group_home_text")


def render_lobby(chat_id: int) -> str:
    lang = get_chat_lang(chat_id)
    s = storage.get_by_chat(chat_id)

    lines = [t(lang, "lobby_title")]
    lines.append(t(lang, "lobby_status", state=str(s.state.value)))
    lines.append("")
    lines.append(t(lang, "lobby_players", n=len(s.players), maxn=s.max_players))
    for i, p in enumerate(s.players.values(), start=1):
        lines.append(f"{i}) {p.name}")
    lines.append("")
    lines.append(t(lang, "lobby_hint") if s.state == GameState.LOBBY else t(lang, "started_hint"))
    return "\n".join(lines)


async def show_group_panel(bot: Bot, chat_id: int) -> None:
    lang = get_chat_lang(chat_id)

    if storage.has_session(chat_id):
        text = render_lobby(chat_id)
        kb = kb_group_lobby(lang)
    else:
        text = render_group_home(chat_id)
        kb = kb_group_home(lang)

    mid = GROUP_PANEL_ID.get(chat_id)
    if mid:
        await safe_edit(bot, chat_id, mid, text, kb)
    else:
        m = await bot.send_message(chat_id, text, reply_markup=kb)
        GROUP_PANEL_ID[chat_id] = m.message_id


async def show_private_panel(bot: Bot, uid: int, chat_id: int) -> None:
    lang = get_user_lang(uid)
    text = t(lang, "private_start_text")
    kb = kb_private_menu(lang)

    mid = PRIVATE_PANEL_ID.get(uid)
    if mid:
        await safe_edit(bot, chat_id, mid, text, kb)
    else:
        m = await bot.send_message(chat_id, text, reply_markup=kb)
        PRIVATE_PANEL_ID[uid] = m.message_id


def err_msg(lang: str, e: Exception) -> str:
    if isinstance(e, SessionNotFound):
        return t(lang, "err_no_game")
    if isinstance(e, SessionAlreadyExists):
        return t(lang, "err_game_exists")
    if isinstance(e, PlayerAlreadyJoined):
        return t(lang, "err_already_joined")
    if isinstance(e, SessionFull):
        return t(lang, "err_full")
    if isinstance(e, NotOwner):
        return t(lang, "err_not_owner")
    if isinstance(e, NotEnoughPlayers):
        return t(lang, "err_need3")
    if isinstance(e, SessionAlreadyStarted):
        return t(lang, "err_started")
    return t(lang, "err_default")


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    me = await bot.get_me()
    print(f"✅ Bot is running: @{me.username} (id={me.id})")

    # default EN menu
    await apply_telegram_commands(bot, DEFAULT_LANG)

    # ----- commands -----
    @dp.message(CommandStart())
    async def cmd_start(message: types.Message):
        if is_group(message.chat):
            set_chat_lang(message.chat.id, get_chat_lang(message.chat.id))
            await show_group_panel(bot, message.chat.id)
            await try_delete(message)
            return

        if message.from_user:
            set_user_lang(message.from_user.id, get_user_lang(message.from_user.id))
            await show_private_panel(bot, message.from_user.id, message.chat.id)

    @dp.message(Command("help"))
    async def cmd_help(message: types.Message):
        if is_group(message.chat):
            lang = get_chat_lang(message.chat.id)
            await show_group_panel(bot, message.chat.id)
            mid = GROUP_PANEL_ID.get(message.chat.id)
            if mid:
                await safe_edit(bot, message.chat.id, mid, t(lang, "help_text"), kb_back(lang, "group"))
            await try_delete(message)
            return

        if message.from_user:
            uid = message.from_user.id
            lang = get_user_lang(uid)
            await show_private_panel(bot, uid, message.chat.id)
            mid = PRIVATE_PANEL_ID.get(uid)
            if mid:
                await safe_edit(bot, message.chat.id, mid, t(lang, "help_text"), kb_back(lang, "pm"))

    @dp.message(Command("rules"))
    async def cmd_rules(message: types.Message):
        if is_group(message.chat):
            lang = get_chat_lang(message.chat.id)
            await show_group_panel(bot, message.chat.id)
            mid = GROUP_PANEL_ID.get(message.chat.id)
            if mid:
                await safe_edit(bot, message.chat.id, mid, t(lang, "rules_text"), kb_back(lang, "group"))
            await try_delete(message)
            return

        if message.from_user:
            uid = message.from_user.id
            lang = get_user_lang(uid)
            await show_private_panel(bot, uid, message.chat.id)
            mid = PRIVATE_PANEL_ID.get(uid)
            if mid:
                await safe_edit(bot, message.chat.id, mid, t(lang, "rules_text"), kb_back(lang, "pm"))

    @dp.message(Command("newgame"))
    async def cmd_newgame(message: types.Message):
        if not is_group(message.chat):
            uid = message.from_user.id if message.from_user else 0
            await message.answer(t(get_user_lang(uid), "only_group_cmd"))
            return

        lang = get_chat_lang(message.chat.id)
        try:
            s = storage.create_session(message.chat.id, message.from_user.id, lang=lang)
            s.add_player(message.from_user.id, safe_name(message.from_user))
            await show_group_panel(bot, message.chat.id)
        except GameError as e:
            await show_group_panel(bot, message.chat.id)
            mid = GROUP_PANEL_ID.get(message.chat.id)
            if mid:
                await safe_edit(bot, message.chat.id, mid, "⚠️ " + err_msg(lang, e), kb_back(lang, "group"))

        await try_delete(message)

    @dp.message(Command("startgame"))
    async def cmd_startgame(message: types.Message):
        if not is_group(message.chat):
            uid = message.from_user.id if message.from_user else 0
            await message.answer(t(get_user_lang(uid), "only_group_cmd"))
            return

        lang = get_chat_lang(message.chat.id)
        try:
            s = storage.get_by_chat(message.chat.id)
            s.start(message.from_user.id)
            await show_group_panel(bot, message.chat.id)
        except GameError as e:
            await show_group_panel(bot, message.chat.id)
            mid = GROUP_PANEL_ID.get(message.chat.id)
            if mid:
                await safe_edit(bot, message.chat.id, mid, "⚠️ " + err_msg(lang, e), kb_back(lang, "group"))

        await try_delete(message)

    # ----- callbacks -----
    @dp.callback_query()
    async def cb(call: types.CallbackQuery):
        if not call.message:
            return

        chat_id = call.message.chat.id
        data = call.data or ""

        # GROUP
        if is_group(call.message.chat):
            lang = get_chat_lang(chat_id)

            if data == "home:newgame":
                try:
                    s = storage.create_session(chat_id, call.from_user.id, lang=lang)
                    s.add_player(call.from_user.id, safe_name(call.from_user))
                    await show_group_panel(bot, chat_id)
                    # ✅ top toast ONLY for create lobby
                    await toast(call, t(lang, "toast_created"))
                except GameError as e:
                    await toast(call, "⚠️ " + err_msg(lang, e))
                return

            if data == "lobby:refresh":
                await show_group_panel(bot, chat_id)
                await toast(call, t(lang, "toast_refreshed"))
                return

            if data == "lobby:join":
                try:
                    s = storage.get_by_chat(chat_id)
                    s.add_player(call.from_user.id, safe_name(call.from_user))
                    await show_group_panel(bot, chat_id)
                    await toast(call, t(lang, "toast_joined"))
                except PlayerAlreadyJoined:
                    await toast(call, t(lang, "toast_already_joined"))
                except GameError as e:
                    await toast(call, "⚠️ " + err_msg(lang, e))
                return

            if data == "lobby:start":
                try:
                    s = storage.get_by_chat(chat_id)
                    s.start(call.from_user.id)
                    await show_group_panel(bot, chat_id)
                    await toast(call, t(lang, "toast_started"))
                except NotEnoughPlayers:
                    await toast(call, t(lang, "toast_need3"))
                except GameError as e:
                    await toast(call, "⚠️ " + err_msg(lang, e))
                return

            if data == "menu:group:commands":
                await safe_edit(bot, chat_id, call.message.message_id, t(lang, "commands_text_group"), kb_back(lang, "group"))
                return

            if data == "menu:group:rules":
                await safe_edit(bot, chat_id, call.message.message_id, t(lang, "rules_text"), kb_back(lang, "group"))
                return

            if data == "menu:group:lang":
                await safe_edit(bot, chat_id, call.message.message_id, t(lang, "lang_choose"), kb_lang(lang, "group"))
                return

            if data == "back:group":
                await show_group_panel(bot, chat_id)
                return

            if data.startswith("lang:group:"):
                new_lang = data.split(":")[-1]
                set_chat_lang(chat_id, new_lang)
                await apply_telegram_commands(bot, new_lang)
                await show_group_panel(bot, chat_id)
                # optional toast for language change (top)
                await toast(call, t(new_lang, "toast_lang_set"))
                return

            return

        # PRIVATE
        uid = call.from_user.id
        lang = get_user_lang(uid)

        if data == "menu:pm:rules":
            await safe_edit(bot, chat_id, call.message.message_id, t(lang, "rules_text"), kb_back(lang, "pm"))
            return

        if data == "menu:pm:lang":

            await safe_edit(bot, chat_id, call.message.message_id, t(lang, "lang_choose"), kb_lang(lang, "pm"))
            return

        if data == "back:pm":
            await show_private_panel(bot, uid, chat_id)
            return

        if data.startswith("lang:pm:"):
            new_lang = data.split(":")[-1]
            set_user_lang(uid, new_lang)
            await apply_telegram_commands(bot, new_lang)
            await show_private_panel(bot, uid, chat_id)
            await toast(call, t(new_lang, "toast_lang_set"))
            return

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
