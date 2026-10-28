
# -*- coding: utf-8 -*-
# FileStreamBot43 - Start Plugin

import logging
from html import escape

from pyrogram import filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message
)
from pyrogram.enums import ParseMode

from WebStreamer.bot import StreamBot
from WebStreamer.vars import Var
from WebStreamer.utils.human_readable import humanbytes
from WebStreamer.utils.database import Database

logger = logging.getLogger(__name__)

db = Database(Var.DATABASE_URL, Var.SESSION_NAME)


# DEBUG: Check whether private Telegram messages reach the bot.
@StreamBot.on_message(filters.private, group=99)
async def debug_private_messages(client, message: Message):
    try:
        logger.info(
            "DEBUG: Private message received. User=%s, Text=%r",
            message.from_user.id if message.from_user else "unknown",
            message.text
        )
    except Exception:
        logger.exception("Private message debug handler failed")


# START command
@StreamBot.on_message(
    filters.command("start") & filters.private,
    group=0
)
async def start_handler(bot: StreamBot, message: Message):
    try:
        logger.info(
            "START command received from user_id=%s",
            message.from_user.id if message.from_user else "unknown"
        )

        if not message.from_user:
            logger.warning("START message has no sender")
            return

        # Register user in MongoDB; continue if registration fails.
        try:
            if not await db.is_user_exist(message.from_user.id):
                await db.add_user(message.from_user.id)
        except Exception:
            logger.exception("MongoDB user registration failed")

        parts = (message.text or "").split(maxsplit=1)
        command_arg = parts[1].strip() if len(parts) > 1 else ""

        # Normal /start command
        if not command_arg:
            updates_channel = Var.UPDATES_CHANNEL

            if updates_channel:
                try:
                    member = await bot.get_chat_member(
                        updates_channel,
                        message.from_user.id
                    )

                    status = str(member.status).lower().split(".")[-1]

                    if status == "kicked":
                        await message.reply_text(
                            "You are banned from using this bot. "
                            "Contact support."
                        )
                        return

                except Exception:
                    logger.exception(
                        "Updates channel membership check failed"
                    )
                    await message.reply_text(
                        "I couldn't verify the Updates Channel membership. "
                        "Please contact the bot owner."
                    )
                    return

            start_text = getattr(
                Var,
                "START_TEXT",
                "Hello {first}! Welcome to the bot."
            )

            text = start_text.format(
                first=escape(message.from_user.first_name or "User"),
                last=escape(message.from_user.last_name or ""),
                username=escape(
                    "@" + message.from_user.username
                    if message.from_user.username else ""
                ),
                id=message.from_user.id
            )

            await message.reply_text(
                text=text,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "Help",
                            callback_data="help"
                        ),
                        InlineKeyboardButton(
                            "About",
                            callback_data="about"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "Source Code",
                            url=(
                                "https://github.com/"
                                "sathish333324678-debug/FileStreamBot43"
                            )
                        )
                    ]
                ]),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            logger.info("START reply sent successfully")
            return

        # Deep link: /start FILE_ID
        try:
            file_id = int(command_arg)
        except ValueError:
            await message.reply_text(
                "Invalid start command or file ID."
            )
            return

        try:
            file_info = await db.get_file(file_id)
        except Exception:
            logger.exception("MongoDB file lookup failed")
            await message.reply_text(
                "Unable to retrieve this file right now. "
                "Please try again later."
            )
            return

        if not file_info:
            await message.reply_text("File not found or deleted.")
            return

        file_name = escape(str(file_info.get("file_name", "File")))
        file_size = humanbytes(file_info.get("file_size", 0))

        base_url = Var.URL.rstrip("/")
        stream_link = f"{base_url}/watch/{file_id}"
        download_link = f"{base_url}/download/{file_id}"

        await message.reply_text(
            text=(
                f"<b>File Name:</b> <code>{file_name}</code>\n"
                f"<b>File Size:</b> {file_size}"
            ),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "Fast Download",
                        url=download_link
                    ),
                    InlineKeyboardButton(
                        "Watch Online",
                        url=stream_link
                    )
                ]
            ]),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

        logger.info("File information reply sent for file_id=%s", file_id)

    except Exception:
        logger.exception("Error inside start_handler")
        try:
            await message.reply_text(
                "Sorry, an error occurred. Please try again later."
            )
        except Exception:
            logger.exception("Could not send error reply")


# HELP command
@StreamBot.on_message(
    filters.command("help") & filters.private,
    group=0
)
async def help_handler(bot: StreamBot, message: Message):
    try:
        logger.info("HELP command received")

        help_text = getattr(
            Var,
            "HELP_TEXT",
            "Send /start to begin using this bot."
        )

        await message.reply_text(
            text=help_text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

    except Exception:
        logger.exception("Error inside help_handler")
        try:
            await message.reply_text(
                "Unable to display help right now."
            )
        except Exception:
            logger.exception("Could not send help reply")


# ABOUT command
@StreamBot.on_message(
    filters.command("about") & filters.private,
    group=0
)
async def about_handler(bot: StreamBot, message: Message):
    try:
        logger.info("ABOUT command received")

        about_text = getattr(
            Var,
            "ABOUT_TEXT",
            "FileStreamBot43"
        )

        await message.reply_text(
            text=about_text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

    except Exception:
        logger.exception("Error inside about_handler")
        try:
            await message.reply_text(
                "Unable to display information right now."
            )
        except Exception:
            logger.exception("Could not send about reply")
