
import urllib.parse
from html import escape

from WebStreamer.bot import StreamBot
from WebStreamer.vars import Var
from WebStreamer.utils.human_readable import humanbytes
from WebStreamer.utils.database import Database

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant


db = Database(Var.DATABASE_URL, Var.SESSION_NAME)


START_TEXT = """
<i>👋 Hᴇʏ, {}</i>

<i>I'ᴍ Tᴇʟᴇɢʀᴀᴍ Fɪʟᴇ Sᴛʀᴇᴀᴍɪɴɢ Bᴏᴛ ᴀɴᴅ Dɪʀᴇᴄᴛ Lɪɴᴋ Gᴇɴᴇʀᴀᴛᴏʀ.</i>

<i>Cʟɪᴄᴋ Hᴇʟᴘ ғᴏʀ ᴍᴏʀᴇ ɪɴғᴏʀᴍᴀᴛɪᴏɴ.</i>

<i><u>𝗪𝗔𝗥𝗡𝗜𝗡𝗚 🚸</u></i>
<b>Use this bot responsibly and follow Telegram's rules.</b>
"""

HELP_TEXT = """
<i>- Send me a video, audio, or document privately.</i>
<i>- I will generate Watch Online and Download links.</i>
<i>- The configured channel and web server must be working.</i>
"""

ABOUT_TEXT = """
<b>⚜ My Name: FileStreamX</b>
<b>🔸 Version: 3.0.1</b>
"""


START_BUTTONS = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("HELP", callback_data="help"),
        InlineKeyboardButton("ABOUT", callback_data="about"),
        InlineKeyboardButton("CLOSE", callback_data="close")
    ]
])

HELP_BUTTONS = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("HOME", callback_data="home"),
        InlineKeyboardButton("ABOUT", callback_data="about"),
        InlineKeyboardButton("CLOSE", callback_data="close")
    ]
])

ABOUT_BUTTONS = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("HOME", callback_data="home"),
        InlineKeyboardButton("HELP", callback_data="help"),
        InlineKeyboardButton("CLOSE", callback_data="close")
    ]
])


def get_media(message):
    return message.video or message.document or message.audio


def get_media_file_name(message):
    media = get_media(message)
    return getattr(media, "file_name", None) if media else None


def get_base_url():
    if Var.ON_HEROKU or Var.NO_PORT:
        return f"https://{Var.FQDN}"
    return f"http://{Var.FQDN}:{Var.PORT}"


async def check_membership(bot, message):
    if Var.UPDATES_CHANNEL == "None":
        return True

    try:
        member = await bot.get_chat_member(
            Var.UPDATES_CHANNEL,
            message.from_user.id
        )
        if str(member.status).lower() == "kicked":
            await message.reply_text("You cannot use this bot.")
            return False
        return True

    except UserNotParticipant:
        await message.reply_text(
            "Please join our updates channel first.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "Join Channel",
                    url=f"https://t.me/{Var.UPDATES_CHANNEL.lstrip('@')}"
                )
            ]])
        )
        return False

    except Exception as error:
        print(f"Membership check error: {error}")
        await message.reply_text(
            "Unable to check channel membership. Please try again."
        )
        return False


@StreamBot.on_callback_query()
async def cb_data(bot, update):
    await update.answer()

    if update.data == "home":
        await update.message.edit_text(
            START_TEXT.format(update.from_user.mention),
            parse_mode=ParseMode.HTML,
            reply_markup=START_BUTTONS
        )
    elif update.data == "help":
        await update.message.edit_text(
            HELP_TEXT,
            parse_mode=ParseMode.HTML,
            reply_markup=HELP_BUTTONS
        )
    elif update.data == "about":
        await update.message.edit_text(
            ABOUT_TEXT,
            parse_mode=ParseMode.HTML,
            reply_markup=ABOUT_BUTTONS
        )
    elif update.data == "close":
        await update.message.delete()


@StreamBot.on_message(filters.command("start") & filters.private)
async def start_handler(bot, message):
    parts = (message.text or "").split(maxsplit=1)
    payload = parts[1] if len(parts) > 1 else ""

    if not payload:
        try:
            if not await db.is_user_exist(message.from_user.id):
                await db.add_user(message.from_user.id)
        except Exception as error:
            print(f"Database user error: {error}")

        if not await check_membership(bot, message):
            return

        await message.reply_text(
            START_TEXT.format(message.from_user.mention),
            parse_mode=ParseMode.HTML,
            reply_markup=START_BUTTONS
        )
        return

    try:
        message_id = int(payload.split("_")[-1])
        media_message = await bot.get_messages(
            Var.BIN_CHANNEL, message_id
        )

        if not media_message or not get_media(media_message):
            await message.reply_text("File not found.")
            return

        if not await check_membership(bot, message):
            return

        name = get_media_file_name(media_message) or "file"
        base_url = get_base_url()

        watch_link = f"{base_url}/watch/{message_id}"
        download_link = f"{base_url}/download/{message_id}"

        await message.reply_text(
            f"<b>File:</b> <code>{escape(name)}</code>\n\n"
            "<b>Choose an option:</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("▶️ Watch Online", url=watch_link),
                InlineKeyboardButton("⬇️ Download", url=download_link)
            ]])
        )
    except Exception as error:
        print(f"Start file handler error: {error}")
        await message.reply_text("Unable to generate the file links.")


@StreamBot.on_message(
    filters.private
    & (filters.video | filters.document | filters.audio)
)
async def auto_link_handler(bot, message):
    try:
        media = get_media(message)
        if not media:
            return

        if not await check_membership(bot, message):
            return

        # Copy the uploaded file into the configured storage channel.
        saved_message = await message.copy(chat_id=Var.BIN_CHANNEL)

        file_name = get_media_file_name(message) or "file"
        file_size = (
            humanbytes(media.file_size)
            if media.file_size else "Unknown"
        )

        base_url = get_base_url()
        watch_link = f"{base_url}/watch/{saved_message.id}"
        download_link = f"{base_url}/download/{saved_message.id}"

        await message.reply_text(
            f"<b>✅ Links generated!</b>\n\n"
            f"<b>📁 File:</b> <code>{escape(file_name)}</code>\n"
            f"<b>📦 Size:</b> {escape(str(file_size))}\n\n"
            "Choose an option below:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("▶️ Watch Online", url=watch_link),
                InlineKeyboardButton("⬇️ Download", url=download_link)
            ]])
        )

    except Exception as error:
        print(f"Auto link handler error: {error}")
        await message.reply_text(
            "Link generation failed. Check the Render logs."
        )


@StreamBot.on_message(filters.command("help") & filters.private)
async def help_handler(bot, message):
    await message.reply_text(
        HELP_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=HELP_BUTTONS
    )


@StreamBot.on_message(filters.command("about") & filters.private)
async def about_handler(bot, message):
    await message.reply_text(
        ABOUT_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=ABOUT_BUTTONS
    )
