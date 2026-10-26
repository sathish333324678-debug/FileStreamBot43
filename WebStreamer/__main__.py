
import os
import sys
import glob
import asyncio
import importlib
from pathlib import Path

from pyrogram import idle
from .bot import StreamBot
from .vars import Var
from aiohttp import web
from .server import web_server
from .utils.keepalive import ping_server


ppath = "WebStreamer/bot/plugins/*.py"
files = glob.glob(ppath)

loop = asyncio.get_event_loop()


async def start_services():
    print("\n")
    print("------------------- Initializing Telegram Bot -------------------")

    await StreamBot.start()

    print("\n")
    print("---------------------- DONE ----------------------")
    print("\n")
    print("------------------- Importing -------------------")

    for name in files:
        with open(name) as file:
            path = Path(file.name)
            plugin_name = path.stem

            plugins_dir = Path(
                f"WebStreamer/bot/plugins/{plugin_name}.py"
            )

            import_path = f".plugins.{plugin_name}"

            spec = importlib.util.spec_from_file_location(
                import_path, plugins_dir
            )

            if spec is None or spec.loader is None:
                raise ImportError(
                    f"Could not load plugin: {plugin_name}"
                )

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            sys.modules[
                "WebStreamer.bot.plugins." + plugin_name
            ] = module

            print("Imported => " + plugin_name)

    print("\n")
    print("------------------- Initializing Web Server -------------------")

    app = web.AppRunner(await web_server())
    await app.setup()

    # Render requires binding to 0.0.0.0, not the public hostname.
    bind_address = "0.0.0.0"

    await web.TCPSite(
        app,
        bind_address,
        Var.PORT
    ).start()

    print("\n")
    print("----------------------- Service Started -----------------------")
    print(
        "Bot => {}".format(
            (await StreamBot.get_me()).first_name
        )
    )
    print(
        "Server => {}:{}".format(
            bind_address,
            Var.PORT
        )
    )

    if Var.ON_HEROKU:
        print("App running on => {}".format(Var.FQDN))
        print("------------------ Starting Keep Alive Service ------------------")
        await asyncio.create_task(ping_server())

    print("---------------------------------------------------------------")

    await idle()


if __name__ == "__main__":
    try:
        loop.run_until_complete(start_services())
    except KeyboardInterrupt:
        print("----------------------- Service Stopped -----------------------")
    finally:
        if not loop.is_closed():
            loop.close()
