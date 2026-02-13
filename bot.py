import os
import asyncio
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from aiogram.types import BotCommand
from aiogram.types.bot_command_scope_chat import BotCommandScopeChat

from storage.memory import InMemoryStorage
from game.session import GameState
from utils.i18n import t

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not set in .env")

storage = InMemoryStorage()

# per-user language for private chat
USER_LANG: dict[int, str] = {}

def is_group(chat: types.Chat) -> bool:
    return chat.type in ("group", "supergroup")

def uname(u: types.User) -> str:
    return f"@{u.username}" if u.username else u.full_name

def get_user_lang(user_id: int) -> str:
    return USER_LANG.get(user_id, "ru")

async def safe_edit(msg: types.Message, text: str, markup: InlineKeyboardMarkup):
    try:
        await msg.edit_text(text, reply_markup=markup)
    except TelegramBadRequest:
        pass

def kb_private_main(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_how"), callback_data="menu:private:how")],
        [
            InlineKeyboardButton(text=t(lang, "btn_rules"), callback_data="menu:private:rules"),
            InlineKeyboardButton(text=t(lang, "btn_commands"), callback_data="menu:private:commands"),
        ],
        [InlineKeyboardButton(text=t(lang, "btn_language"), callback_data="menu:private:lang")]
    ])

def kb_group_start(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_create_game"), callback_data="group:newgame")],
        [
            InlineKeyboardButton(text=t(lang, "btn_rules"), callback_data="menu:group:rules"),
            InlineKeyboardButton(text=t(lang, "btn_commands"), callback_data="menu:group:commands"),
        ],
        [InlineKeyboardButton(text=t(lang, "btn_language"), callback_data="menu:group:lang")]
    ])

def kb_lang(scope: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Русский", callback_data=f"lang:{scope}:ru"),
            InlineKeyboardButton(text="English", callback_data=f"lang:{scope}:en"),
            InlineKeyboardButton(text="עברית", callback_data=f"lang:{scope}:he"),
        ],
        [InlineKeyboardButton(text="⬅️ Back", callback_data=f"menu:{scope}:home")]
    ])

def kb_back(scope: str, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data=f"menu:{scope}:home")]
    ])

def panel_text(session) -> str:
    lang = session.lang
    lines = [
        t(lang, "panel_title"),
        "",
        t(lang, "panel_status", state=session.state.value),
        t(lang, "panel_players", count=len(session.players), max=session.max_players),
        ""
    ]
    for i, p in enumerate(session.players, start=1):
        lines.append(f"{i}) {p.username}")
    lines += ["", t(lang, "panel_hint_started" if session.state == GameState.STARTED else "panel_hint_lobby")]
    return "\n".join(lines)

def kb_panel(session) -> InlineKeyboardMarkup:
    lang = session.lang
    can_start = (session.state == GameState.LOBBY and len(session.players) >= 3)
    start_cb = "lobby:start" if can_start else "noop:need3"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t(lang, "btn_join"), callback_data="lobby:join"),
            InlineKeyboardButton(text=t(lang, "btn_start"), callback_data=start_cb),
        ],
        [
            InlineKeyboardButton(text=t(lang, "btn_players"), callback_data="lobby:players"),
            InlineKeyboardButton(text=t(lang, "btn_refresh"), callback_data="lobby:refresh"),
        ],
        [
            InlineKeyboardButton(text=t(lang, "btn_language"), callback_data="menu:group:lang"),
            InlineKeyboardButton(text=t(lang, "btn_commands"), callback_data="menu:group:commands"),
        ],
    ])

async def ensure_panel(bot: Bot, session):
    if session.panel_message_id is None:
        m = await bot.send_message(session.chat_id, panel_text(session), reply_markup=kb_panel(session))
        session.panel_message_id = m.message_id
    else:
        try:
            await bot.edit_message_text(
                chat_id=session.chat_id,
                message_id=session.panel_message_id,
                text=panel_text(session),
                reply_markup=kb_panel(session)
            )
        except TelegramBadRequest:
            pass

async def set_commands_for_chat(bot: Bot, chat_id: int, lang: str):
    # Menu language per-chat (this is what you wanted)
    if lang == "ru":
        cmds = [
            BotCommand(command="start", description="Меню / Инструкция"),
            BotCommand(command="newgame", description="Создать игру (группа)"),
            BotCommand(command="players", description="Обновить панель"),
            BotCommand(command="startgame", description="Старт (создатель)"),
            BotCommand(command="rules", description="Правила"),
            BotCommand(command="help", description="Помощь"),
        ]
    elif lang == "he":
        cmds = [
            BotCommand(command="start", description="תפריט / הוראות"),
            BotCommand(command="newgame", description="יצירת משחק (קבוצה)"),
            BotCommand(command="players", description="רענון פאנל"),
            BotCommand(command="startgame", description="התחלה (בעלים)"),
            BotCommand(command="rules", description="חוקים"),
            BotCommand(command="help", description="עזרה"),
        ]
    else:
        cmds = [
            BotCommand(command="start", description="Menu / Instructions"),
            BotCommand(command="newgame", description="Create game (group)"),
            BotCommand(command="players", description="Refresh panel"),
            BotCommand(command="startgame", description="Start (host)"),
            BotCommand(command="rules", description="Rules"),
            BotCommand(command="help", description="Help"),
        ]

    await bot.set_my_commands(cmds, scope=BotCommandScopeChat(chat_id=chat_id))

async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    me = await bot.get_me()
    print(f"✅ Bot is running: @{me.username} (id={me.id})")

    @dp.message(CommandStart())
    async def start(message: types.Message):
        if is_group(message.chat):
            lang = "ru"
            await set_commands_for_chat(bot, message.chat.id, lang)
            await message.answer(
                f"{t(lang,'group_welcome_title')}\n\n{t(lang,'group_welcome_text')}",
                reply_markup=kb_group_start(lang)
            )
            return

        lang = get_user_lang(message.from_user.id)
        await set_commands_for_chat(bot, message.chat.id, lang)
        await message.answer(
            f"{t(lang,'private_welcome_title')}\n\n{t(lang,'private_welcome_text')}",
            reply_markup=kb_private_main(lang)
        )

    @dp.message(Command("help"))
    async def help_cmd(message: types.Message):
        lang = get_user_lang(message.from_user.id) if message.chat.type == "private" else "ru"
        await set_commands_for_chat(bot, message.chat.id, lang)
        await message.answer(
            f"{t(lang,'commands_title')}\n\n{t(lang,'commands_text')}\n\n{t(lang,'rules_text')}",
            reply_markup=(kb_private_main(lang) if message.chat.type == "private" else kb_group_start(lang))
        )

    @dp.message(Command("rules"))
    async def rules_cmd(message: types.Message):
        lang = get_user_lang(message.from_user.id) if message.chat.type == "private" else "ru"
        await set_commands_for_chat(bot, message.chat.id, lang)
        await message.answer(
            f"{t(lang,'rules_title')}\n\n{t(lang,'rules_text')}",
            reply_markup=(kb_private_main(lang) if message.chat.type == "private" else kb_group_start(lang))
        )

    @dp.message(Command("newgame"))
    async def newgame(message: types.Message):
        if not is_group(message.chat):
            lang = get_user_lang(message.from_user.id)
            await message.answer(t(lang, "private_welcome_text"), reply_markup=kb_private_main(lang))
            return

        session = storage.get(message.chat.id)
        if session is None:
            session = storage.create(message.chat.id, message.from_user.id)
            session.lang = "ru"

        session.add_player(message.from_user.id, uname(message.from_user))
        await set_commands_for_chat(bot, message.chat.id, session.lang)
        await ensure_panel(bot, session)

    @dp.message(Command("players"))
    async def players_cmd(message: types.Message):
        if not is_group(message.chat):
            return
        session = storage.get(message.chat.id)
        if session:
            await ensure_panel(bot, session)

    @dp.message(Command("startgame"))
    async def startgame_cmd(message: types.Message):
        if not is_group(message.chat):
            return
        session = storage.get(message.chat.id)
        if not session:
            return
        if not session.is_owner(message.from_user.id):
            return
        if len(session.players) < 3:
            return
        session.state = GameState.STARTED
        await ensure_panel(bot, session)

    @dp.callback_query()
    async def cb(call: types.CallbackQuery):
        if not call.message:
            return

        async def toast(text: str, alert: bool = False):
            try:
                await call.answer(text, show_alert=alert)
            except Exception:
                pass

        chat = call.message.chat
        data = call.data or ""

        # -------- PRIVATE UI --------
        if chat.type == "private":
            lang = get_user_lang(call.from_user.id)

            if data == "menu:private:home":
                await set_commands_for_chat(call.bot, chat.id, lang)
                await safe_edit(call.message, f"{t(lang,'private_welcome_title')}\n\n{t(lang,'private_welcome_text')}", kb_private_main(lang))
                return

            if data == "menu:private:how":
                await safe_edit(call.message, f"{t(lang,'private_welcome_title')}\n\n{t(lang,'private_welcome_text')}", kb_back("private", lang))
                return

            if data == "menu:private:rules":
                await safe_edit(call.message, f"{t(lang,'rules_title')}\n\n{t(lang,'rules_text')}", kb_back("private", lang))
                return

            if data == "menu:private:commands":
                await safe_edit(call.message, f"{t(lang,'commands_title')}\n\n{t(lang,'commands_text')}", kb_back("private", lang))
                return

            if data == "menu:private:lang":
                await safe_edit(call.message, t(lang, "lang_choose"), kb_lang("private"))
                return

            if data.startswith("lang:private:"):
                new_lang = data.split(":")[-1]
                USER_LANG[call.from_user.id] = new_lang
                await set_commands_for_chat(call.bot, chat.id, new_lang)
                await safe_edit(call.message, f"{t(new_lang,'private_welcome_title')}\n\n{t(new_lang,'private_welcome_text')}", kb_private_main(new_lang))
                await toast(t(new_lang, "lang_set"))
                return

            await toast("")
            return

        # -------- GROUP UI --------
        session = storage.get(chat.id)
        group_lang = session.lang if session else "ru"

        if data == "menu:group:home":
            await set_commands_for_chat(call.bot, chat.id, group_lang)
            await safe_edit(call.message, f"{t(group_lang,'group_welcome_title')}\n\n{t(group_lang,'group_welcome_text')}", kb_group_start(group_lang))
            return

        if data == "group:newgame":
            if session is None:
                session = storage.create(chat.id, call.from_user.id)
                session.lang = "ru"
            session.add_player(call.from_user.id, uname(call.from_user))
            await set_commands_for_chat(call.bot, chat.id, session.lang)
            await ensure_panel(call.bot, session)
            await toast("✅")
            return

        if data == "menu:group:rules":
            await safe_edit(call.message, f"{t(group_lang,'rules_title')}\n\n{t(group_lang,'rules_text')}", kb_group_start(group_lang))
            return

        if data == "menu:group:commands":
            await safe_edit(call.message, f"{t(group_lang,'commands_title')}\n\n{t(group_lang,'commands_text')}", kb_group_start(group_lang))
            return

        if data == "menu:group:lang":
            # owner only (if session exists)
            if session and not session.is_owner(call.from_user.id):
                await toast(t(session.lang, "toast_owner_only"), alert=True)
                return
            await safe_edit(call.message, t(group_lang, "lang_choose"), kb_lang("group"))
            return

        if data.startswith("lang:group:"):
            if not session:
                await toast(t(group_lang, "toast_no_game"), alert=True)
                return
            if not session.is_owner(call.from_user.id):
                await toast(t(session.lang, "toast_owner_only"), alert=True)
                return
            new_lang = data.split(":")[-1]
            session.lang = new_lang
            await set_commands_for_chat(call.bot, chat.id, new_lang)
            await ensure_panel(call.bot, session)
            await toast(t(new_lang, "lang_set"))
            return

        # lobby buttons require session
        if data == "noop:need3":
            if session:
                await toast(t(session.lang, "toast_need_three"), alert=True)
            else:
                await toast(t(group_lang, "toast_no_game"), alert=True)
            return

        if not session:
            await toast(t(group_lang, "toast_no_game"), alert=True)
            return

        glang = session.lang

        if data == "lobby:refresh":
            await ensure_panel(call.bot, session)
            await toast("🔄")
            return

        if data == "lobby:players":
            names = "\n".join([p.username for p in session.players]) or "-"
            await toast(names, alert=True)  # popup only to clicker
            return

        if data == "lobby:join":
            r = session.add_player(call.from_user.id, uname(call.from_user))
            if r == "full":
                await toast(t(glang, "toast_full"), alert=True)
                return
            if r == "exists":
                await toast(t(glang, "toast_already_joined"), alert=True)
            else:
                await toast(t(glang, "toast_joined"))
            await ensure_panel(call.bot, session)
            return

        if data == "lobby:start":
            if not session.is_owner(call.from_user.id):
                await toast(t(glang, "toast_owner_only"), alert=True)
                return
            if len(session.players) < 3:
                await toast(t(glang, "toast_need_three"), alert=True)
                return
            session.state = GameState.STARTED
            await ensure_panel(call.bot, session)
            await toast("🚀")
            return

        await toast("")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
