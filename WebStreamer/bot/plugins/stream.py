
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
            f"Nᴇᴡ Usᴇʀ Jᴏɪɴᴇᴅ :\n\n"
            f"Nᴀᴍᴇ : [{m.from_user.first_name}]"
            f"(tg://user?id={m.from_user.id}) Sᴛᴀʀᴛᴇᴅ Yᴏᴜʀ Bᴏᴛ !!"
        )

    if Var.UPDATES_CHANNEL != "None":
        try:
            user = await c.get_chat_member(
                Var.UPDATES_CHANNEL, m.chat.id
            )

            if user.status == "kicked":
                await c.send_message(
                    chat_id=m.chat.id,
                    text=(
                        "__Sᴏʀʀʏ Sɪʀ, Yᴏᴜ ᴀʀᴇ Bᴀɴɴᴇᴅ "
                        "ᴛᴏ ᴜsᴇ ᴍᴇ.__\n\n"
                        "**Cᴏɴᴛᴀᴄᴛ Dᴇᴠᴇʟᴏᴘᴇʀ "
                        "@greymatters_bots_discussion Tʜᴇʏ "
                        "Wɪʟʟ Hᴇʟᴘ Yᴏᴜ**"
                    ),
                    parse_mode="markdown",
                    disable_web_page_preview=True
                )
                return

        except UserNotParticipant:
            await c.send_message(
                chat_id=m.chat.id,
                text=(
                    "<i>Jᴏɪɴ ᴍʏ ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ "
                    "ᴛᴏ ᴜꜱᴇ ᴍᴇ 🔐</i>"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "Jᴏɪɴ ɴᴏᴡ 🔓",
                            url=f"https://t.me/{Var.UPDATES_CHANNEL}"
                        )
                    ]
                ]),
                parse_mode="HTML"
            )
            return

        except Exception:
            await c.send_message(
                chat_id=m.chat.id,
                text=(
                    "**Sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ Wʀᴏɴɢ. "
                    "Cᴏɴᴛᴀᴄᴛ ᴍʏ ʙᴏss** "
                    "@greymatters_bots_discussion"
                ),
                parse_mode="markdown",
                disable_web_page_preview=True
            )
            return

    try:
        log_msg = await m.forward(chat_id=Var.BIN_CHANNEL)

        file_name = get_media_file_name(m)
        file_size = humanbytes(get_media_file_size(m))

        if Var.ON_HEROKU or Var.NO_PORT:
            stream_link = (
                f"https://{Var.FQDN}/"
                f"{log_msg.message_id}/{file_name}"
            )
        else:
            stream_link = (
                f"http://{Var.FQDN}:{Var.PORT}/"
                f"{log_msg.message_id}/{file_name}"
            )

        msg_text = """
<i><u>𝗬𝗼𝘂𝗿 𝗟𝗶𝗻𝗸 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱 !</u></i>

<b>📂 Fɪʟᴇ ɴᴀᴍᴇ :</b> <i>{}</i>

<b>📦 Fɪʟᴇ ꜱɪᴢᴇ :</b> <i>{}</i>

<b>📥 Dᴏᴡɴʟᴏᴀᴅ :</b> <i>{}</i>

<b>🚸 Nᴏᴛᴇ : Tʜɪs ᴘᴇʀᴍᴀɴᴇɴᴛ Lɪɴᴋ, Nᴏᴛ Exᴘɪʀᴇᴅ</b>

<i>© @GreyMatter_bots</i>
"""

        await log_msg.reply_text(
            text=(
                f"**RᴇQᴜᴇꜱᴛᴇᴅ ʙʏ :** "
                f"[{m.from_user.first_name}]"
                f"(tg://user?id={m.from_user.id})\n"
                f"**Uꜱᴇʀ ɪᴅ :** `{m.from_user.id}`\n"
                f"**Dᴏᴡɴʟᴏᴀᴅ ʟɪɴᴋ :** {stream_link}"
            ),
            disable_web_page_preview=True,
            parse_mode="Markdown",
            quote=True
        )

        await m.reply_text(
            text=msg_text.format(
                file_name or "Unknown",
                file_size or "Unknown",
                stream_link
            ),
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "Dᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ 📥",
                        url=stream_link
                    )
                ]
            ]),
            quote=True
        )

    except FloodWait as e:
        print(f"Sleeping for {e.value}s")
        await asyncio.sleep(e.value)
        await c.send_message(
            chat_id=Var.BIN_CHANNEL,
            text=(
                f"Gᴏᴛ FʟᴏᴏᴅWᴀɪᴛ ᴏғ {e.value}s "
                f"from [{m.from_user.first_name}]"
                f"(tg://user?id={m.from_user.id})\n\n"
                f"**𝚄𝚜𝚎𝚛 𝙸𝙳 :** `{m.from_user.id}`"
            ),
            disable_web_page_preview=True,
            parse_mode="Markdown"
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
        log_msg = await broadcast.forward(chat_id=Var.BIN_CHANNEL)

        me = await bot.get_me()
        bot_username = me.username

        if Var.ON_HEROKU or Var.NO_PORT:
            stream_link = (
                f"https://{Var.FQDN}/{log_msg.message_id}"
            )
        else:
            stream_link = (
                f"http://{Var.FQDN}:{Var.PORT}/"
                f"{log_msg.message_id}"
            )

        start_link = (
            f"https://t.me/{bot_username}"
            f"?start=Moksh_b658_{log_msg.message_id}"
        )

        await log_msg.reply_text(
            text=(
                f"**Cʜᴀɴɴᴇʟ Nᴀᴍᴇ:** `{broadcast.chat.title}`\n"
                f"**Cʜᴀɴɴᴇʟ ID:** `{broadcast.chat.id}`\n"
                f"**Rᴇǫᴜᴇsᴛ ᴜʀʟ:** {start_link}"
            ),
            quote=True,
            parse_mode="Markdown"
        )

        await bot.edit_message_reply_markup(
            chat_id=broadcast.chat.id,
            message_id=broadcast.id,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "Dᴏᴡɴʟᴏᴀᴅ ʟɪɴᴋ 📥",
                        url=start_link
                    )
                ]
            ])
        )

    except FloodWait as w:
        print(f"Sleeping for {w.value}s")
        await asyncio.sleep(w.value)

        await bot.send_message(
            chat_id=Var.BIN_CHANNEL,
            text=(
                f"Gᴏᴛ FʟᴏᴏᴅWᴀɪᴛ ᴏғ {w.value}s "
                f"from {broadcast.chat.title}\n\n"
                f"**Cʜᴀɴɴᴇʟ ID:** `{broadcast.chat.id}`"
            ),
            disable_web_page_preview=True,
            parse_mode="Markdown"
        )

    except Exception as e:
        await bot.send_message(
            chat_id=Var.BIN_CHANNEL,
            text=f"**#ᴇʀʀᴏʀ_ᴛʀᴀᴄᴇʙᴀᴄᴋ:** `{e}`",
            disable_web_page_preview=True,
            parse_mode="Markdown"
        )
        print(
            f"Cᴀɴ'ᴛ Eᴅɪᴛ Bʀᴏᴀᴅᴄᴀsᴛ Mᴇssᴀɢᴇ!\n"
            f"Eʀʀᴏʀ: {e}"
        )
