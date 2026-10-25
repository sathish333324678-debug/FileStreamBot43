Python

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

<i><b>🍃 Bᴏᴛ Mᴀɪɴᴛᴀɪɴᴇᴅ Bʏ:</b> @GreyMatter_bots</i>
"""

HELP_TEXT = """
<i>- Sᴇɴᴅ ᴍᴇ ᴀɴʏ ғɪʟᴇ ᴏʀ ᴍᴇᴅɪᴀ ғʀᴏᴍ Tᴇʟᴇɢʀᴀᴍ.</i>
<i>- I ᴡɪʟʟ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴅᴏᴡɴʟᴏᴀᴅ ᴏʀ sᴛʀᴇᴀᴍ ʟɪɴᴋ ᴡʜᴇɴ ᴄᴏɴғɪɢᴜʀᴇᴅ ᴄᴏʀʀᴇᴄᴛʟʏ.</i>
<i>- File links require the file to be available in the configured channel.</i>

<i><b>Contact support for issues:</b>
<a href="https://t.me/greymatters_bots_discussion">Click here</a></i>
"""

ABOUT_TEXT = """
<b>⚜ Mʏ Nᴀᴍᴇ: FileStreamX</b>

<b>🔸 Vᴇʀsɪᴏɴ: 3.0.1</b>
<b>🔹 Sᴏᴜʀᴄᴇ: <a href="https://bit.ly/3MeXqmu">Click Here</a></b>
<b>🔸 GɪᴛHᴜʙ: <a href="https://github.com/avipatilpro">Follow</a></b>
<b>🔹 Dᴇᴠᴇʟᴏᴘᴇʀ: <a href="https://t.me/GreyMatter_Owner">GreyMatter_Owner</a></b>
"""


START_BUTTONS = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("Hᴇʟᴘ", callback_data="help"),
        InlineKeyboardButton("Aʙᴏᴜᴛ", callback_data="about"),
        InlineKeyboardButton("Cʟᴏsᴇ", callback_data="close")
    ]
])

HELP_BUTTONS = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("Hᴏᴍᴇ", callback_data="home"),
        InlineKeyboardButton("Aʙᴏᴜᴛ", callback_data="about"),
        InlineKeyboardButton("Cʟᴏsᴇ", callback_data="close")
    ]
])

ABOUT_BUTTONS = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("Hᴏᴍᴇ", callback_data="home"),
        InlineKeyboardButton("Hᴇʟᴘ", callback_data="help"),
        InlineKeyboardButton("Cʟᴏsᴇ", callback_data="close")
    ]
])


@StreamBot.on_callback_query()
async def cb_data(bot, update):
    await update.answer()

    if update.data == "home":
        await update.message.edit_text(
            text=START_TEXT.format(update.from_user.mention),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=START_BUTTONS
        )

    elif update.data == "help":
        await update.message.edit_text(
            text=HELP_TEXT,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=HELP_BUTTONS
        )

    elif update.data == "about":
        await update.message.edit_text(
            text=ABOUT_TEXT,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=ABOUT_BUTTONS
        )

    elif update.data == "close":
        await update.message.delete()


def get_media_file_size(message):
    media = message.video or message.audio or message.document

    if media and media.file_size:
        return media.file_size

    return None


def get_media_file_name(message):
    media = message.video or message.document or message.audio

    if media and media.file_name:
        return urllib.parse.quote(media.file_name, safe="")

    return None


async def check_membership(bot, message):
    if Var.UPDATES_CHANNEL == "None":
        return True

    try:
        member = await bot.get_chat_member(
            Var.UPDATES_CHANNEL,
            message.from_user.id
        )

        if member.status == "kicked":
            await message.reply_text(
                "Sorry, you are banned from using this bot."
            )
            return False

        return True

    except UserNotParticipant:
        await message.reply_text(
            "Please join the updates channel to use this bot.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "Join channel",
                        url=f"https://t.me/{Var.UPDATES_CHANNEL.lstrip('@')}"
                    )
                ]
            ])
        )
        return False

    except Exception as error:
        print(f"Membership check error: {error}")
        await message.reply_text(
            "Could not check channel membership. Please try again later."
        )
        return False


@StreamBot.on_message(filters.command("start") & filters.private)
async def start_handler(bot, message):

    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id)

        try:
            await bot.send_message(
                Var.BIN_CHANNEL,
                f"New user joined:\n\n"
                f"Name: {message.from_user.first_name}\n"
                f"User ID: {message.from_user.id}"
            )
        except Exception as error:
            print(f"New user notification error: {error}")

    parts = (message.text or "").split(maxsplit=1)
    payload = parts[1] if len(parts) > 1 else ""

    if not payload:
        if not await check_membership(bot, message):
            return

        await message.reply_text(
            text=START_TEXT.format(message.from_user.mention),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=START_BUTTONS
        )
        return

    try:
        message_id = int(payload.split("_")[-1])
    except (ValueError, IndexError):
        await message.reply_text("Invalid file link.")
        return

    if not await check_membership(bot, message):
        return

    try:
        media_message = await bot.get_messages(
            chat_id=Var.BIN_CHANNEL,
            message_ids=message_id
        )

        if not media_message or not (
            media_message.document
            or media_message.video
            or media_message.audio
        ):
            await message.reply_text(
                "File not found. The link may be invalid."
            )
            return

        raw_name = get_media_file_name(media_message)
        file_name = raw_name or "file"
        file_size = humanbytes(
            get_media_file_size(media_message)
        ) or "Unknown"

        if Var.ON_HEROKU or Var.NO_PORT:
            stream_link = (
                f"https://{Var.FQDN}/"
                f"{media_message.id}/{file_name}"
            )
        else:
            stream_link = (
                f"http://{Var.FQDN}:{Var.PORT}/"
                f"{media_message.id}/{file_name}"
            )

        msg_text = (
            "<b><u>Your Link Generated!</u></b>\n\n"
            f"<b>📂 File Name:</b> <code>{escape(file_name)}</code>\n\n"
            f"<b>📦 File Size:</b> <i>{escape(str(file_size))}</i>\n\n"
            f"<b>📥 Download:</b>\n"
            f"<a href=\"{escape(stream_link, quote=True)}\">"
            "Click here to download</a>\n\n"
            "<i>© @GreyMatter_bots</i>"
        )

        await message.reply_text(
            text=msg_text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "Download Now 📥",
                        url=stream_link
                    )
                ]
            ])
        )

    except Exception as error:
        print(f"Start file handler error: {error}")
        await message.reply_text(
            "Unable to retrieve this file right now. "
            "Please try again later."
        )


@StreamBot.on_message(filters.command("about") & filters.private)
async def about_handler(bot, message):
    await message.reply_text(
        text=ABOUT_TEXT,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=ABOUT_BUTTONS
    )


@StreamBot.on_message(filters.command("help") & filters.private)
async def help_handler(bot, message):
    await message.reply_text(
        text=HELP_TEXT,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=HELP_BUTTONS
    )
