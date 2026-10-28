
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
PLUGIN_PATH = BASE_DIR / "bot" / "plugins"


async def load_plugins():
    files = sorted(PLUGIN_PATH.glob("*.py"))

    if not files:
        raise RuntimeError(f"No plugins found in {PLUGIN_PATH}")

    for path in files:
        if path.name.startswith("_"):
            continue

        plugin_name = path.stem
        import_path = f"WebStreamer.bot.plugins.{plugin_name}"

        spec = importlib.util.spec_from_file_location(import_path, path)

        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load plugin: {plugin_name}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[import_path] = module
        spec.loader.exec_module(module)

        logger.info("Plugin loaded: %s", plugin_name)


async def main():
    app_runner = None
    ping_task = None
    bot_started = False

    try:
        logger.info("Loading Telegram Bot plugins...")
        await load_plugins()

        logger.info("Starting Telegram Bot...")
        await StreamBot.start()
        bot_started = True

        me = await StreamBot.get_me()
        logger.info(
            "Bot started successfully: @%s",
            me.username or me.first_name
        )

        logger.info("Starting Web Server...")
        app = await web_server()

        app_runner = web.AppRunner(app)
        await app_runner.setup()

        site = web.TCPSite(
            app_runner,
            host=Var.BIND_ADRESS,
            port=Var.PORT
        )
        await site.start()

        logger.info("Web server running on port %s", Var.PORT)
        logger.info("Service Started Successfully.")

        if Var.ON_HEROKU:
            ping_task = asyncio.create_task(ping_server())

        await idle()

    except asyncio.CancelledError:
        logger.info("Service cancellation received.")
        raise

    except Exception:
        logger.exception("Service failed")
        raise

    finally:
        logger.info("Stopping services...")

        if ping_task is not None:
            ping_task.cancel()
            with suppress(asyncio.CancelledError):
                await ping_task

        if app_runner is not None:
            with suppress(Exception):
                await app_runner.cleanup()

        if bot_started:
            try:
                if StreamBot.is_connected:
                    await StreamBot.stop()
            except Exception:
                logger.exception("Error while stopping Telegram Bot")

        logger.info("Service shutdown completed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Service stopped by keyboard interrupt.")
