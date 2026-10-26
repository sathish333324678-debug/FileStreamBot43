
import logging
import mimetypes
import os
from urllib.parse import quote

from aiohttp import web

from ..vars import Var
from ..bot import StreamBot
from ..utils.custom_dl import TGCustomYield, chunk_size, offset_fix

routes = web.RouteTableDef()


@routes.get("/", allow_head=True)
async def root_route_handler(request):
    bot_details = await StreamBot.get_me()
    return web.json_response({
        "status": "running",
        "Telegram_Bot": "@" + bot_details.username
    })


@routes.get("/watch/{message_id:\\d+}", allow_head=True)
async def watch_handler(request):
    return await media_streamer(request, int(request.match_info["message_id"]), False)


@routes.get("/download/{message_id:\\d+}", allow_head=True)
async def download_handler(request):
    return await media_streamer(request, int(request.match_info["message_id"]), True)


@routes.get("/{message_id:\\d+}", allow_head=True)
@routes.get("/{message_id:\\d+}/{name}", allow_head=True)
async def legacy_stream_handler(request):
    return await media_streamer(request, int(request.match_info["message_id"]), True)


async def media_streamer(request, message_id: int, force_download: bool):
    try:
        media_msg = await StreamBot.get_messages(
            Var.BIN_CHANNEL, message_id
        )

        if not media_msg or not (
            media_msg.document or media_msg.video or media_msg.audio
        ):
            raise web.HTTPNotFound(text="Video not found")

        props = await TGCustomYield().generate_file_properties(media_msg)
        file_size = props.file_size
        file_name = props.file_name or "video.mp4"
        mime_type = props.mime_type or mimetypes.guess_type(file_name)[0] or "application/octet-stream"

        range_header = request.headers.get("Range")
        start = 0
        end = file_size - 1

        if range_header:
            try:
                unit, ranges = range_header.split("=", 1)
                if unit != "bytes":
                    raise ValueError("Unsupported range")
                start_text, end_text = ranges.split("-", 1)

                if start_text:
                    start = int(start_text)
                if end_text:
                    end = int(end_text)
                if start < 0 or end < start or start >= file_size:
                    raise ValueError("Invalid range")
                end = min(end, file_size - 1)
            except (ValueError, TypeError):
                raise web.HTTPRequestRangeNotSatisfiable(
                    headers={"Content-Range": f"bytes */{file_size}"}
                )

        length = end - start + 1
        size = await chunk_size(length)
        offset = await offset_fix(start, size)
        first_cut = start - offset
        last_cut = (end % size) + 1
        count = (length + first_cut + size - 1) // size

        body = TGCustomYield().yield_file(
            media_msg, offset, first_cut, last_cut, count, size
        )

        disposition = "attachment" if force_download else "inline"
        headers = {
            "Content-Type": mime_type,
            "Content-Disposition": f"{disposition}; filename*=UTF-8''{quote(file_name)}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(length),
        }

        if range_header:
            headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"

        response = web.StreamResponse(
            status=206 if range_header else 200,
            headers=headers,
        )
        await response.prepare(request)

        async for part in body:
            await response.write(part)

        await response.write_eof()
        return response

    except web.HTTPException:
        raise
    except Exception:
        logging.exception("Video streaming failed for message %s", message_id)
        raise web.HTTPInternalServerError(text="Unable to stream this file")
