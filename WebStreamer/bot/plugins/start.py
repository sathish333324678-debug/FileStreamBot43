# -*- coding: utf-8 -*-
# (c) @SpEcHiDe

import asyncio
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.enums import ParseMode

from WebStreamer.vars import Var
from WebStreamer.utils.human_readable import humanbytes
from WebStreamer.utils.database import Database

db = Database(Var.DATABASE_URL, Var.SESSION_NAME)

@Client.on_message(filters.command('start') & filters.private)
async def start(bot: Client, message: Message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id)
        
    usr_cmd = message.text.split("_")[-1]
    if usr_cmd == "/start":
        if Var.UPDATES_CHANNEL is not None:
            try:
                user = await bot.get_chat_member(Var.UPDATES_CHANNEL, message.from_user.id)
                if user.status == "kicked":
                    await message.reply_text(
                        text="You are banned from using this bot. Contact support.",
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                    return
            except Exception:
                button = [[InlineKeyboardButton("Join Updates Channel", url=f"https://t.me/{Var.UPDATES_CHANNEL}")]]
                markup = InlineKeyboardMarkup(button)
                await message.reply_text(
                    text="<b>You must join my updates channel to use me</b>",
                    reply_markup=markup,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                return

        await message.reply_text(
            text=Var.START_TEXT.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                id=message.from_user.id
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton('Help', callback_data='help'),
                        InlineKeyboardButton('About', callback_data='about')
                    ],
                    [
                        InlineKeyboardButton('Source Code', url='https://github.com/SpEcHiDe/PublicLeech')
                    ]
                ]
            ),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        return

    try:
        file_id = int(usr_cmd)
        file_info = await db.get_file(file_id)
        if not file_info:
            await message.reply_text("File not found or deleted.")
            return
            
        file_name = file_info.get('file_name', 'File')
        file_size = humanbytes(file_info.get('file_size', 0))
        
        stream_link = f"{Var.URL}watch/{file_id}"
        download_link = f"{Var.URL}download/{file_id}"
        
        buttons = [
            [
                InlineKeyboardButton("Fast Download", url=download_link),
                InlineKeyboardButton("Watch Online", url=stream_link)
            ]
        ]
        
        await message.reply_text(
            text=f"<b>File Name:</b> <code>{file_name}</code>\n<b>File Size:</b> {file_size}",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        
    except ValueError:
        await message.reply_text(
            text="Invalid start command or file ID.",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await message.reply_text(
            text=f"Something went wrong: <code>{e}</code>",
            parse_mode=ParseMode.HTML
        )

@Client.on_message(filters.command('help') & filters.private)
async def help_handler(bot: Client, message: Message):
    await message.reply_text(
        text=Var.HELP_TEXT,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )

@Client.on_message(filters.command('about') & filters.private)
async def about_handler(bot: Client, message: Message):
    await message.reply_text(
        text=Var.ABOUT_TEXT,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )

