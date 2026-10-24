# (c) @AvishkarPatil

import asyncio
import urllib.parse

from WebStreamer.bot import StreamBot
from WebStreamer.utils.database import Database
from WebStreamer.utils.human_readable import humanbytes
from WebStreamer.vars import Var

from pyrogram import filters, Client
from pyrogram.errors import FloodWait, UserNotParticipant
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

db = Database(Var.DATABASE_URL, Var.SESSION_NAME)


def get_media_file_size(m):
    media = m.video or m.audio or m.document
    if media and media.file_size:
        return media.file_size
    return None


def get_media_file_name(m):
    media = m.video or m.document or m.audio
    if media and media.file_name:
        return urllib.parse.quote_plus(media.file_name)
    return None


@StreamBot.on_message(
    filters.private & (filters.document | filters.video | filters.audio),
    group=4
)
async def private_receive_handler(c: Client, m: Message):

    if not await db.is_user_exist(m.from_user.id):
        await db.add_user(m.from_user.id)
        await c.send_message(
            Var.BIN_CHANNEL,
            f"New User Joined:\n\n"
            f"Name: {m.from_user.first_name}\n"
            f"Started Your Bot!"
        )

    if Var.UPDATES_CHANNEL != "None":
        try:
            user = await c.get_chat_member(
                Var.UPDATES_CHANNEL,
                m.from_user.id
            )

            if user.status == "kicked":
                await c.send_message(
                    chat_id=m.chat.id,
                    text=(
                        "Sorry, you are banned from using this bot.\n\n"
                        "Contact @greymatters_bots_discussion for help."
                    ),
                    disable_web_page_preview=True
                )
                return

        except UserNotParticipant:
            await c.send_message(
                chat_id=m.chat.id,
                text="Join my updates channel to use this bot 🔐",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "Join Now 🔓",
                            url=f"https://t.me/{Var.UPDATES_CHANNEL}"
                        )
                    ]
                ])
            )
            return

        except Exception as e:
            print(f"Channel membership check failed: {e}")
            await c.send_message(
                chat_id=m.chat.id,
                text="Something went wrong. Please contact the bot owner."
            )
            return

    try:
        log_msg = await m.forward(chat_id=Var.BIN_CHANNEL)

        file_name = get_media_file_name(m) or "file"
        file_size = humanbytes(get_media_file_size(m))

        if Var.ON_HEROKU or Var.NO_PORT:
            stream_link = (
                f"https://{Var.FQDN}/"
                f"{log_msg.id}/{file_name}"
            )
        else:
            stream_link = (
                f"http://{Var.FQDN}:{Var.PORT}/"
                f"{log_msg.id}/{file_name}"
            )

        msg_text = """
<b><u>Your Link Generated!</u></b>

<b>📂 File Name:</b> <i>{}</i>

<b>📦 File Size:</b> <i>{}</i>

<b>📥 Download:</b> <i>{}</i>

<b>🚸 Note:</b> This link may remain available while the bot and stored file are accessible.

<i>© @GreyMatter_bots</i>
"""

        await log_msg.reply_text(
            text=(
                f"**Requested by:** "
                f"[{m.from_user.first_name}]"
                f"(tg://user?id={m.from_user.id})\n"
                f"**User ID:** `{m.from_user.id}`\n"
                f"**Download Link:** {stream_link}"
            ),
            disable_web_page_preview=True,
            parse_mode="Markdown",
            quote=True
        )

        await m.reply_text(
            text=msg_text.format(
                file_name,
                file_size or "Unknown",
                stream_link
            ),
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "Download Now 📥",
                        url=stream_link
                    )
                ]
            ]),
            quote=True
        )

    except FloodWait as e:
        print(f"Sleeping for {e.value} seconds")
        await asyncio.sleep(e.value)

    except Exception as e:
        print(f"Private file handler error: {e}")
        await c.send_message(
            chat_id=Var.BIN_CHANNEL,
            text=f"Private file handler error: {e}"
        )


@StreamBot.on_message(
    filters.channel & (filters.document | filters.video),
    group=-1
)
async def channel_receive_handler(bot: Client, broadcast: Message):

    if int(broadcast.chat.id) in Var.BANNED_CHANNELS:
        await bot.leave_chat(broadcast.chat.id)
        return

    try:
        log_msg = await broadcast.forward(
            chat_id=Var.BIN_CHANNEL
        )

        bot_info = await bot.get_me()
        bot_username = bot_info.username

        start_link = (
            f"https://t.me/{bot_username}"
            f"?start=Moksh_b658_{log_msg.id}"
        )

        await log_msg.reply_text(
            text=(
                f"**Channel Name:** `{broadcast.chat.title}`\n"
                f"**Channel ID:** `{broadcast.chat.id}`\n"
                f"**Request URL:** {start_link}"
            ),
            quote=True,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

        await bot.edit_message_reply_markup(
            chat_id=broadcast.chat.id,
            message_id=broadcast.id,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "Download Link 📥",
                        url=start_link
                    )
                ]
            ])
        )

    except FloodWait as e:
        print(f"Sleeping for {e.value} seconds")
        await asyncio.sleep(e.value)

    except Exception as e:
        print(f"Channel handler error: {e}")
        await bot.send_message(
            chat_id=Var.BIN_CHANNEL,
            text=f"Channel handler error: {e}"
        )
