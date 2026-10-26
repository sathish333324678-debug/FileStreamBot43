
import asyncio
import logging
import mimetypes
from urllib.parse import quote

from aiohttp import web
from aiohttp.client_exceptions import ClientConnectionResetError

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
    return await media_streamer(
        request,
        int(request.match_info["message_id"]),
        False
    )


@routes.get("/download/{message_id:\\d+}", allow_head=True)
async def download_handler(request):
    return await media_streamer(
        request,
        int(request.match_info["message_id"]),
        True
    )


@routes.get("/{message_id:\\d+}", allow_head=True)
@routes.get("/{message_id:\\d+}/{name}", allow_head=True)
async def legacy_stream_handler(request):
    return await media_streamer(
        request,
        int(request.match_info["message_id"]),
        True
    )


async def media_streamer(request, message_id: int, force_download: bool):
    try:
        media_msg = await StreamBot.get_messages(
            Var.BIN_CHANNEL,
            message_id
        )

        if not media_msg or not (
            media_msg.document
            or media_msg.video
            or media_msg.audio
        ):
            raise web.HTTPNotFound(text="Video not found")

        file_helper = TGCustomYield()
        props = await file_helper.generate_file_properties(media_msg)

        file_size = props.file_size
        file_name = props.file_name or "video.mp4"
        mime_type = (
            props.mime_type
            or mimetypes.guess_type(file_name)[0]
            or "application/octet-stream"
        )

        if file_size <= 0:
            raise web.HTTPInternalServerError(
                text="Invalid file size"
            )

        range_header = request.headers.get("Range")
        start = 0
        end = file_size - 1

        if range_header:
            try:
                unit, ranges = range_header.split("=", 1)

                if unit.strip() != "bytes":
                    raise ValueError("Unsupported range unit")

                if "," in ranges:
                    raise ValueError("Multiple ranges are unsupported")

                start_text, end_text = ranges.split("-", 1)

                if not start_text:
                    # Suffix range, e.g. bytes=-500
                    suffix_length = int(end_text)

                    if suffix_length <= 0:
                        raise ValueError("Invalid suffix range")

                    start = max(0, file_size - suffix_length)
                else:
                    start = int(start_text)

                if end_text and start_text:
                    end = int(end_text)

                if (
                    start < 0
                    or start >= file_size
                    or end < start
                ):
                    raise ValueError("Invalid byte range")

                end = min(end, file_size - 1)

            except (ValueError, TypeError):
                raise web.HTTPRequestRangeNotSatisfiable(
                    headers={
                        "Content-Range": f"bytes */{file_size}"
                    }
                )

        length = end - start + 1

        size = await chunk_size(length)
        offset = await offset_fix(start, size)

        first_cut = start - offset
        last_cut = (end % size) + 1
        count = (length + first_cut + size - 1) // size

        body = file_helper.yield_file(
            media_msg,
            offset,
            first_cut,
            last_cut,
            count,
            size
        )

        disposition = "attachment" if force_download else "inline"

        headers = {
            "Content-Type": mime_type,
            "Content-Disposition": (
                f"{disposition}; filename*=UTF-8''{quote(file_name)}"
            ),
            "Accept-Ranges": "bytes",
            "Content-Length": str(length),
        }

        status = 200

        if range_header:
            status = 206
            headers["Content-Range"] = (
                f"bytes {start}-{end}/{file_size}"
            )

        response = web.StreamResponse(
            status=status,
            headers=headers
        )

        await response.prepare(request)

        try:
            async for part in body:
                await response.write(part)

            await response.write_eof()

        except (
            ClientConnectionResetError,
            ConnectionResetError,
            BrokenPipeError,
        ):
            # The browser/client disconnected during streaming.
            logging.info(
                "Client disconnected while streaming message %s",
                message_id
            )

        except asyncio.CancelledError:
            # Allow aiohttp to cancel the request cleanly.
            raise

        return response

    except web.HTTPException:
        raise

    except (
        ClientConnectionResetError,
        ConnectionResetError,
        BrokenPipeError,
    ):
        logging.info(
            "Client disconnected while preparing message %s",
            message_id
        )
        return web.Response(status=499)

    except asyncio.CancelledError:
        raise

    except Exception:
        logging.exception(
            "Video streaming failed for message %s",
            message_id
        )
        raise web.HTTPInternalServerError(
            text="Unable to stream this file"
        )
