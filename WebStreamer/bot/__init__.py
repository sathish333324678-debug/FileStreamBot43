
from pyrogram import Client
from ..vars import Var
import logging

logger = logging.getLogger(__name__)

StreamBot = Client(
    name="Web Streamer",
    api_id=Var.API_ID,
    api_hash=Var.API_HASH,
    bot_token=Var.BOT_TOKEN,
    sleep_threshold=Var.SLEEP_THRESHOLD,
    workers=Var.WORKERS
)

logger.info("StreamBot client configured successfully")
