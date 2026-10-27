
import logging

from pyrogram import Client, filters
from ..vars import Var

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

StreamBot = Client(
    name="Web Streamer",
    api_id=Var.API_ID,
    api_hash=Var.API_HASH,
    bot_token=Var.BOT_TOKEN,
    sleep_threshold=Var.SLEEP_THRESHOLD,
    workers=Var.WORKERS,
)


@StreamBot.on_message(filters.private, group=999)
async def debug_private_messages(client, message):
    logger.info(
        "DEBUG: Private message received | "
        "chat_id=%s | text=%r | media=%s",
        message.chat.id,
        message.text,
        bool(message.media),
    )
