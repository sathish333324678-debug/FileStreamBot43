
# (c) @AvishkarPatil

import os
import time
import string
import random
import asyncio
import aiofiles
import datetime

from WebStreamer.utils.broadcast_helper import send_msg
from WebStreamer.utils.database import Database
from WebStreamer.bot import StreamBot
from WebStreamer.vars import Var
from pyrogram import filters, Client
from pyrogram.types import Message

db = Database(Var.DATABASE_URL, Var.SESSION_NAME)
broadcast_ids = {}


@StreamBot.on_message(
    filters.command("status")
    & filters.private
    & filters.user(Var.OWNER_ID)
)
async def sts(c: Client, m: Message):
    total_users = await db.total_users_count()

    await m.reply_text(
        text=f"**Total Users in DB:** `{total_users}`",
        parse_mode="Markdown",
        quote=True
    )


@StreamBot.on_message(
    filters.command("broadcast")
    & filters.private
    & filters.user(Var.OWNER_ID)
    & filters.reply
)
async def broadcast_(c: Client, m: Message):
    all_users = await db.get_all_users()
    broadcast_msg = m.reply_to_message

    while True:
        broadcast_id = ''.join(
            random.choice(string.ascii_letters)
            for _ in range(3)
        )
        if not broadcast_ids.get(broadcast_id):
            break

    out = await m.reply_text(
        "Broadcast initiated! You will be notified when all users are processed."
    )

    start_time = time.time()
    total_users = await db.total_users_count()
    done = 0
    failed = 0
    success = 0

    broadcast_ids[broadcast_id] = {
        "total": total_users,
        "current": done,
        "failed": failed,
        "success": success
    }

    try:
        async with aiofiles.open(
            "broadcast.txt", "w", encoding="utf-8"
        ) as broadcast_log_file:

            async for user in all_users:
                try:
                    status, msg = await send_msg(
                        user_id=int(user["id"]),
                        message=broadcast_msg
                    )

                    if msg is not None:
                        await broadcast_log_file.write(str(msg))

                    if status == 200:
                        success += 1
                    else:
                        failed += 1

                    if status == 400:
                        await db.delete_user(user["id"])

                except Exception as e:
                    failed += 1
                    await broadcast_log_file.write(
                        f"User {user.get('id', 'unknown')}: {e}\n"
                    )

                done += 1

                if broadcast_ids.get(broadcast_id) is None:
                    break

                broadcast_ids[broadcast_id].update({
                    "current": done,
                    "failed": failed,
                    "success": success
                })

        completed_in = datetime.timedelta(
            seconds=int(time.time() - start_time)
        )

        await asyncio.sleep(2)
        await out.delete()

        result_text = (
            f"Broadcast completed in `{completed_in}`\n\n"
            f"Total users: {total_users}\n"
            f"Processed: {done}\n"
            f"Success: {success}\n"
            f"Failed: {failed}"
        )

        if failed == 0:
            await m.reply_text(
                text=result_text,
                quote=True
            )
        else:
            await m.reply_document(
                document="broadcast.txt",
                caption=result_text,
                quote=True
            )

    finally:
        broadcast_ids.pop(broadcast_id, None)

        if os.path.exists("broadcast.txt"):
            os.remove("broadcast.txt")
