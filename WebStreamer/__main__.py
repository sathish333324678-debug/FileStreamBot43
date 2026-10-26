
import sys
import glob
import asyncio
import importlib.util
import logging
from pathlib import Path
from contextlib import suppress

from pyrogram import idle
from aiohttp import web

from .bot import StreamBot
from .vars import Var
from .server import web_server
from .utils.keepalive import ping_server

logging.basicConfig(level=logging.INFO)

PLUGIN_PATH = "WebStreamer/bot/plugins/*.py"


async def load_plugins():
    files = sorted(glob.glob(PLUGIN_PATH))

    if not files:
        logging.warning("No plugins found at %s", PLUGIN_PATH)
        return

    for filename in files:
        path = Path(filename)
        plugin_name = path.stem
        import_path = f"WebStreamer.bot.plugins.{plugin_name}"

        spec = importlib.util.spec_from_file_location(
            import_path, path
        )

        if spec is None or spec.loader is None:
            raise ImportError(
                f"Could not load plugin: {plugin_name}"
            )

        module = importlib.util.module_from_spec(spec)
        sys.modules[import_path] = module
        spec.loader.exec_module(module)

        logging.info("Plugin loaded: %s", plugin_name)


async def main():
    app_runner = None
    ping_task = None
    bot_started = False

    try:
        logging.info("Loading Telegram Bot plugins...")
        await load_plugins()

        logging.info("Starting Telegram Bot...")
        await StreamBot.start()
        bot_started = True

        me = await StreamBot.get_me()
        logging.info(
            "Bot started successfully: @%s",
            me.username or me.first_name
        )

        logging.info("Starting Web Server...")
        app = await web_server()

        app_runner = web.AppRunner(app)
        await app_runner.setup()

        site = web.TCPSite(
            app_runner,
            "0.0.0.0",
            Var.PORT
        )
        await site.start()

        logging.info(
            "Web server running on port %s",
            Var.PORT
        )
        logging.info("Service Started Successfully.")

        if Var.ON_HEROKU:
            ping_task = asyncio.create_task(ping_server())

        # Keep the Telegram bot running until shutdown.
        await idle()

    except asyncio.CancelledError:
        logging.info("Service cancellation received.")
        raise

    except Exception:
        logging.exception("Service failed")

    finally:
        logging.info("Stopping services...")

        if ping_task is not None:
            ping_task.cancel()
            with suppress(asyncio.CancelledError):
                await ping_task

        if app_runner is not None:
            with suppress(Exception):
                await app_runner.cleanup()

        if bot_started and StreamBot.is_connected:
            with suppress(Exception):
                await StreamBot.stop()

        logging.info("Service shutdown completed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Service stopped by keyboard interrupt.")
