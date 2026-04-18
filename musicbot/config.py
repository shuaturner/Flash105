from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    discord_token: str
    discord_server_id: int | None
    lavalink_host: str
    lavalink_port: int
    lavalink_password: str
    lavalink_secured: bool
    log_level: str


def load_settings() -> Settings:
    load_dotenv()

    discord_token = os.getenv("DISCORD_TOKEN", "").strip()
    if not discord_token:
        raise RuntimeError("DISCORD_TOKEN is required.")

    server_value = os.getenv("DISCORD_SERVER_ID", "").strip()
    server_id = int(server_value) if server_value else None

    lavalink_host = os.getenv("LAVALINK_HOST", "lavalink").strip() or "lavalink"
    lavalink_port = int(os.getenv("LAVALINK_PORT", "2333").strip() or "2333")
    lavalink_password = os.getenv("LAVALINK_PASSWORD", "youshallnotpass").strip() or "youshallnotpass"
    lavalink_secured = os.getenv("LAVALINK_SECURED", "false").strip().lower() in {"1", "true", "yes", "on"}

    settings = Settings(
        discord_token=discord_token,
        discord_server_id=server_id,
        lavalink_host=lavalink_host,
        lavalink_port=lavalink_port,
        lavalink_password=lavalink_password,
        lavalink_secured=lavalink_secured,
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
    )

    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    return settings
