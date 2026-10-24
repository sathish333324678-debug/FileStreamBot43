import time
import shutil
import psutil
from pyrogram import filters
from pyrogram.types import Message
from WebStreamer.bot import StreamBot
from WebStreamer.vars import Var
from WebStreamer.utils.database import Database

db = Database(Var.DATABASE_URL, Var.SESSION_NAME)

@StreamBot.on_message(filters.command("status") & filters.private & filters.user(Var.OWNER_ID))
async def bot_status(bot: StreamBot, message: Message):
    uptime = time.strftime("%Hh %Mm %Ss", time.gmtime(time.time() - psutil.boot_time()))
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/')
    
    total_users = await db.total_users_count()
    
    status_text = (
        f"**📊 Bot Status**\n\n"
        f"⏳ **Uptime:** `{uptime}`\n"
        f"💻 **CPU Usage:** `{cpu}%`\n"
        f"🧠 **RAM Usage:** `{ram}%`\n"
        f"💾 **Disk Usage:** `{disk.percent}%` ({disk.used // (2**30)}GB / {disk.total // (2**30)}GB)\n\n"
        f"👥 **Total Users:** `{total_users}`"
    )
    
    await message.reply_text(status_text)
