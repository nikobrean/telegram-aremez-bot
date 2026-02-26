import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Optional, List

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from aiogram.types import BotCommand
from aiogram.types import BotCommandScopeDefault, BotCommandScopeAllPrivateChats

from storage.memory import InMemoryStorage
from game.errors import (
    GameError,
    SessionAlreadyExists,
    SessionNotFound,
    AlreadyInSession,
    PlayerAlreadyJoined,
    NotOwner,
    NotEnoughPlayers,
    SessionAlreadyStarted,
)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not found in .env")

DEFAULT_LANG = "en"
SUPPORTED_LANGS = ("en", "ru", "he")

storage = InMemoryStorage()

# one “panel message” per user (edited instead of spam)
PRIVATE_PANEL_ID: Dict[int, int] = {}

# language per user
USER_LANG: Dict[int, str] = {}

BOT_USERNAME: Optional[str] = None


# -------------------- i18n --------------------
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
        pass


async def try_delete_message(bot: Bot, chat_id: int, message_id: int) -> None:
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception:
        pass


async def try_delete(msg: types.Message) -> None:
    try:
        await msg.delete()
    except Exception:
        pass


async def toast(call: types.CallbackQuery, text: str) -> None:
    # top notification, no “OK” popup
    try:
        await call.answer(text, show_alert=False)
    except Exception:
        pass


# -------------------- Telegram command menu --------------------
def build_private_commands(lang: str) -> List[BotCommand]:
    return [
        BotCommand(command="start", description=t(lang, "cmd_start_desc")),
        BotCommand(command="newgame", description=t(lang, "cmd_newgame_desc")),
        BotCommand(command="startgame", description=t(lang, "cmd_startgame_desc")),
        BotCommand(command="help", description=t(lang, "cmd_help_desc")),
        BotCommand(command="rules", description=t(lang, "cmd_rules_desc")),
    ]


async def apply_commands(bot: Bot) -> None:
    for lc in SUPPORTED_LANGS:
        await bot.set_my_commands(build_private_commands(lc), scope=BotCommandScopeAllPrivateChats(), language_code=lc)
    await bot.set_my_commands(build_private_commands(DEFAULT_LANG), scope=BotCommandScopeDefault(), language_code=None)


# -------------------- Keyboards --------------------
def kb_main_menu(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_newgame"), callback_data="menu:newgame")],
        [InlineKeyboardButton(text=t(lang, "btn_rules"), callback_data="menu:rules")],
        [InlineKeyboardButton(text=t(lang, "btn_language"), callback_data="menu:lang")],
    ])


def kb_lang(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="English", callback_data="lang:en"),
            InlineKeyboardButton(text="Русский", callback_data="lang:ru"),
            InlineKeyboardButton(text="עברית", callback_data="lang:he"),
        ],
        [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back:home")],
    ])


def kb_back(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back:home")]
    ])


def kb_invite(lang: str, code: str) -> InlineKeyboardMarkup:
    # must be URL to work when forwarded
    url = f"https://t.me/{BOT_USERNAME}?start=join_{code}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_join_game"), url=url)]
    ])


def kb_host_lobby(lang: str, started: bool) -> InlineKeyboardMarkup:
    # Invite = callback -> sends invite message again
    if started:
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=t(lang, "btn_refresh"), callback_data="lobby:refresh"),
                InlineKeyboardButton(text=t(lang, "btn_end"), callback_data="lobby:end"),
            ],
            [
                InlineKeyboardButton(text=t(lang, "btn_rules"), callback_data="menu:rules"),
                InlineKeyboardButton(text=t(lang, "btn_language"), callback_data="menu:lang"),
            ],
        ])

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_invite"), callback_data="lobby:invite")],
        [
            InlineKeyboardButton(text=t(lang, "btn_start"), callback_data="lobby:start"),
            InlineKeyboardButton(text=t(lang, "btn_refresh"), callback_data="lobby:refresh"),
        ],
        [
            InlineKeyboardButton(text=t(lang, "btn_end"), callback_data="lobby:end"),
        ],
        [
            InlineKeyboardButton(text=t(lang, "btn_rules"), callback_data="menu:rules"),
            InlineKeyboardButton(text=t(lang, "btn_language"), callback_data="menu:lang"),
        ],
    ])


def kb_player_lobby(lang: str, started: bool) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_refresh"), callback_data="lobby:refresh")],
        [
            InlineKeyboardButton(text=t(lang, "btn_rules"), callback_data="menu:rules"),
            InlineKeyboardButton(text=t(lang, "btn_language"), callback_data="menu:lang"),
        ],
    ])


# -------------------- Rendering --------------------
def render_home(lang: str) -> str:
    return t(lang, "private_start_text")


def render_host_lobby(lang: str, players: List[str], min_p: int, max_p: int, started: bool) -> str:
    if not started:
        plist = "\n".join(f"{i+1}) {p}" for i, p in enumerate(players)) if players else t(lang, "lobby_empty")
        return t(lang, "host_lobby_text", players=plist, n=len(players), minp=min_p, maxp=max_p)
    plist = "\n".join(f"{i+1}) {p}" for i, p in enumerate(players)) if players else ""
    return t(lang, "host_ingame_text", players=plist, n=len(players), minp=min_p, maxp=max_p)


def render_player_lobby(lang: str, started: bool) -> str:
    return t(lang, "player_wait_text_started" if started else "player_wait_text")


async def show_private_panel(bot: Bot, uid: int, chat_id: int, *, force_new: bool = False) -> None:
    """
    force_new=True -> delete old panel and send a new one (so it appears at the bottom)
    """
    lang = get_user_lang(uid)

    sess = storage.get_session_for_player(uid)
    if not sess:
        text = render_home(lang)
        kb = kb_main_menu(lang)
    else:
        is_owner = (sess.owner_id == uid)
        players = [p.username for p in sess.players]
        started = sess.started

        if is_owner:
            text = render_host_lobby(lang, players, sess.min_players, sess.max_players, started)
            kb = kb_host_lobby(lang, started)
        else:
            text = render_player_lobby(lang, started)
            kb = kb_player_lobby(lang, started)

    old_mid = PRIVATE_PANEL_ID.get(uid)

    if force_new and old_mid:
        await try_delete_message(bot, chat_id, old_mid)
        old_mid = None
        PRIVATE_PANEL_ID.pop(uid, None)

    if old_mid:
        await safe_edit(bot, chat_id, old_mid, text, kb)
    else:
        m = await bot.send_message(chat_id, text, reply_markup=kb)
        PRIVATE_PANEL_ID[uid] = m.message_id


def err_text(lang: str, e: Exception) -> str:
    if isinstance(e, SessionAlreadyExists):
        return t(lang, "err_owner_has_game")
    if isinstance(e, SessionNotFound):
        return t(lang, "err_no_game")
    if isinstance(e, AlreadyInSession):
        return t(lang, "err_already_in_session")
    if isinstance(e, PlayerAlreadyJoined):
        return t(lang, "err_already_joined")
    if isinstance(e, NotOwner):
        return t(lang, "err_not_owner")
    if isinstance(e, NotEnoughPlayers):
        return t(lang, "err_need_players")
    if isinstance(e, SessionAlreadyStarted):
        return t(lang, "err_started")
    return t(lang, "err_default")


# -------------------- Main --------------------
async def main() -> None:
    global BOT_USERNAME

    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    me = await bot.get_me()
    BOT_USERNAME = me.username
    print(f"✅ Bot is running: @{me.username} (id={me.id})")

    await apply_commands(bot)

    # ----- Commands -----
    @dp.message(CommandStart())
    async def cmd_start(message: types.Message):
        uid = message.from_user.id
        lang = get_user_lang(uid)

        parts = (message.text or "").split(maxsplit=1)
        if len(parts) == 2 and parts[1].startswith("join_"):
            code = parts[1].replace("join_", "").strip().upper()

            current = storage.get_session_for_player(uid)
            if current:
                # if same game -> just show panel, no "already in game"
                if current.code == code:
                    await show_private_panel(bot, uid, message.chat.id)
                    return
                note = await message.answer("⚠️ " + err_text(lang, AlreadyInSession()))
                await asyncio.sleep(2)
                await try_delete(note)
                await show_private_panel(bot, uid, message.chat.id)
                return

            try:
                storage.join_by_code(code, uid, message.from_user.username)
                note = await message.answer(t(lang, "toast_joined"))
                await asyncio.sleep(1)
                await try_delete(note)
            except GameError as e:
                note = await message.answer("⚠️ " + err_text(lang, e))
                await asyncio.sleep(2)
                await try_delete(note)

            await show_private_panel(bot, uid, message.chat.id)
            return

        # ✅ IMPORTANT: if a game exists, /start should re-send lobby panel to bottom
        has_game = storage.get_session_for_player(uid) is not None
        await show_private_panel(bot, uid, message.chat.id, force_new=has_game)

    @dp.message(Command("newgame"))
    async def cmd_newgame(message: types.Message):
        uid = message.from_user.id
        lang = get_user_lang(uid)

        try:
            sess = storage.create_session(owner_id=uid)
            storage.join_by_code(sess.code, uid, message.from_user.username)  # host joins automatically
        except GameError as e:
            note = await message.answer("⚠️ " + err_text(lang, e))
            await asyncio.sleep(2)
            await try_delete(note)
            await show_private_panel(bot, uid, message.chat.id)
            return

        invite_text = t(lang, "invite_text")
        await message.answer(invite_text, reply_markup=kb_invite(lang, sess.code))
        await show_private_panel(bot, uid, message.chat.id, force_new=True)

    @dp.message(Command("startgame"))
    async def cmd_startgame(message: types.Message):
        uid = message.from_user.id
        lang = get_user_lang(uid)

        sess = storage.get_session_for_player(uid)
        if not sess:
            note = await message.answer("⚠️ " + t(lang, "err_no_game"))
            await asyncio.sleep(2)
            await try_delete(note)
            await show_private_panel(bot, uid, message.chat.id)
            return

        try:
            sess.start(uid)

            failed = 0
            for p in sess.players:
                plang = get_user_lang(p.telegram_id)
                cards = sess.hands.get(p.telegram_id, [])
                dm_text = (
                    f"{t(plang, 'dm_cards_title')}\n"
                    + "\n".join(f"• {c}" for c in cards)
                    + t(plang, "dm_cards_footer")
                )
                try:
                    await bot.send_message(p.telegram_id, dm_text)
                except Exception:
                    failed += 1

            await show_private_panel(bot, uid, message.chat.id)

            if failed > 0:
                warn = t(lang, "warn_cant_dm", n=failed)
                note = await message.answer(warn)
                await asyncio.sleep(4)
                await try_delete(note)

        except GameError as e:
            note = await message.answer("⚠️ " + err_text(lang, e))
            await asyncio.sleep(2)
            await try_delete(note)
            await show_private_panel(bot, uid, message.chat.id)

    @dp.message(Command("help"))
    async def cmd_help(message: types.Message):
        uid = message.from_user.id
        lang = get_user_lang(uid)
        await show_private_panel(bot, uid, message.chat.id)
        mid = PRIVATE_PANEL_ID.get(uid)
        if mid:
            await safe_edit(bot, message.chat.id, mid, t(lang, "help_text"), kb_back(lang))

    @dp.message(Command("rules"))
    async def cmd_rules(message: types.Message):
        uid = message.from_user.id
        lang = get_user_lang(uid)
        await show_private_panel(bot, uid, message.chat.id)
        mid = PRIVATE_PANEL_ID.get(uid)
        if mid:
            await safe_edit(bot, message.chat.id, mid, t(lang, "rules_text"), kb_back(lang))

    # ----- Callbacks -----
    @dp.callback_query()
    async def callbacks(call: types.CallbackQuery):
        if not call.message:
            return

        uid = call.from_user.id
        chat_id = call.message.chat.id
        lang = get_user_lang(uid)
        data = call.data or ""

        if data == "menu:newgame":
            try:
                sess = storage.create_session(owner_id=uid)
                storage.join_by_code(sess.code, uid, call.from_user.username)
            except GameError as e:
                await toast(call, "⚠️ " + err_text(lang, e))
                await show_private_panel(bot, uid, chat_id)
                return

            invite_text = t(lang, "invite_text")
            await call.message.answer(invite_text, reply_markup=kb_invite(lang, sess.code))
            await show_private_panel(bot, uid, chat_id, force_new=True)
            await toast(call, t(lang, "toast_created"))
            return

        if data == "lobby:invite":
            sess = storage.get_session_for_player(uid)
            if not sess:
                await toast(call, "⚠️ " + t(lang, "err_no_game"))
                await show_private_panel(bot, uid, chat_id)
                return

            invite_text = t(lang, "invite_text")
            await call.message.answer(invite_text, reply_markup=kb_invite(lang, sess.code))
            await toast(call, t(lang, "toast_invite_sent"))
            return

        if data == "lobby:refresh":
            await show_private_panel(bot, uid, chat_id)
            await toast(call, t(lang, "toast_refreshed"))
            return

        if data == "lobby:end":
            sess = storage.get_session_for_player(uid)
            if not sess:
                await toast(call, "⚠️ " + t(lang, "err_no_game"))
                await show_private_panel(bot, uid, chat_id)
                return
            if sess.owner_id != uid:
                await toast(call, "⚠️ " + t(lang, "err_not_owner"))
                await show_private_panel(bot, uid, chat_id)
                return

            storage.end_session(sess.code)
            await show_private_panel(bot, uid, chat_id, force_new=True)
            await toast(call, t(lang, "toast_ended"))
            return

        if data == "lobby:start":
            sess = storage.get_session_for_player(uid)
            if not sess:
                await toast(call, "⚠️ " + t(lang, "err_no_game"))
                await show_private_panel(bot, uid, chat_id)
                return

            try:
                sess.start(uid)

                failed = 0
                for p in sess.players:
                    plang = get_user_lang(p.telegram_id)
                    cards = sess.hands.get(p.telegram_id, [])
                    dm_text = (
                        f"{t(plang, 'dm_cards_title')}\n"
                        + "\n".join(f"• {c}" for c in cards)
                        + t(plang, "dm_cards_footer")
                    )
                    try:
                        await bot.send_message(p.telegram_id, dm_text)
                    except Exception:
                        failed += 1

                await show_private_panel(bot, uid, chat_id)
                await toast(call, t(lang, "toast_started"))

                if failed > 0:
                    warn = t(lang, "warn_cant_dm", n=failed)
                    note = await call.message.answer(warn)
                    await asyncio.sleep(4)
                    await try_delete(note)

            except GameError as e:
                await toast(call, "⚠️ " + err_text(lang, e))
                await show_private_panel(bot, uid, chat_id)

            return

        if data == "menu:rules":
            mid = PRIVATE_PANEL_ID.get(uid)
            if mid:
                await safe_edit(bot, chat_id, mid, t(lang, "rules_text"), kb_back(lang))
            return

        if data == "menu:lang":
            mid = PRIVATE_PANEL_ID.get(uid)
            if mid:
                await safe_edit(bot, chat_id, mid, t(lang, "lang_choose"), kb_lang(lang))
            return

        if data == "back:home":
            await show_private_panel(bot, uid, chat_id)
            return

        if data.startswith("lang:"):
            new_lang = data.split(":")[-1]
            set_user_lang(uid, new_lang)
            await show_private_panel(bot, uid, chat_id)
            await toast(call, t(new_lang, "toast_lang_set"))
            return

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())