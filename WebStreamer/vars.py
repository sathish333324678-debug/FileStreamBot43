
# (c) @AvishkarPatil | @EverythingSuckz
# FileStreamBot43 - Configuration

import os
from os import getenv, environ


class Var:
    # Telegram API configuration
    API_ID = int(getenv("API_ID", "0"))
    API_HASH = getenv("API_HASH", "")
    BOT_TOKEN = getenv("BOT_TOKEN", "")

    # Session configuration
    SESSION_NAME = getenv("SESSION_NAME", "Moksh_b658")

    # Pyrogram settings
    SLEEP_THRESHOLD = int(getenv("SLEEP_THRESHOLD", "60"))
    WORKERS = int(getenv("WORKERS", "4"))

    # Telegram channels
    BIN_CHANNEL = int(getenv("BIN_CHANNEL", "0"))
    OWNER_ID = int(getenv("OWNER_ID", "797848243"))

    # Web server settings (Render)
    PORT = int(getenv("PORT", "8080"))
    BIND_ADRESS = getenv("WEB_SERVER_BIND_ADDRESS", "0.0.0.0")
    NO_PORT = getenv("NO_PORT", "False").lower() in (
        "true", "1", "yes"
    )

    # Heroku detection
    APP_NAME = None
    ON_HEROKU = "DYNO" in environ

    if ON_HEROKU:
        APP_NAME = getenv("APP_NAME", "")
        FQDN = f"{APP_NAME}.herokuapp.com" if APP_NAME else ""
    else:
        FQDN = getenv("FQDN", "filestreambot43.onrender.com")

    # Public website URL
    URL = getenv(
        "URL",
        "https://filestreambot43.onrender.com"
    ).rstrip("/") + "/"

    # Database
    DATABASE_URL = getenv("DATABASE_URL", "")

    # Ping interval
    PING_INTERVAL = int(getenv("PING_INTERVAL", "500"))

    # Updates channel: empty or "None" means no channel check
    UPDATES_CHANNEL = getenv("UPDATES_CHANNEL", "").strip()

    if UPDATES_CHANNEL.lower() in ("", "none", "null"):
        UPDATES_CHANNEL = None

    # Banned channels
    BANNED_CHANNELS = list(
        {
            int(channel_id)
            for channel_id in getenv(
                "BANNED_CHANNELS", "-1001296894100"
            ).split()
            if channel_id.lstrip("-").isdigit()
        }
    )
