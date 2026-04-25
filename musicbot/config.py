from __future__ import annotations

import logging
import os
import re
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
    auto_join_track_url: str | None
    auto_join_channel_id: int | None
    auto_join_user_id: int | None
    runtime_config_path: str
    log_level: str


def parse_optional_discord_id(value: str) -> int | None:
    cleaned = value.strip()
    if not cleaned:
        return None

    if cleaned.isdigit():
        return int(cleaned)

    match = re.search(r"(\d{15,})$", cleaned)
    if match:
        return int(match.group(1))

    raise ValueError(f"Invalid Discord ID value: {cleaned}")


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
    auto_join_track_url = os.getenv("AUTO_JOIN_TRACK_URL", "").strip() or None
    auto_join_channel_id = parse_optional_discord_id(os.getenv("AUTO_JOIN_CHANNEL_ID", ""))
    auto_join_user_id = parse_optional_discord_id(os.getenv("AUTO_JOIN_USER_ID", ""))

    settings = Settings(
        discord_token=discord_token,
        discord_server_id=server_id,
        lavalink_host=lavalink_host,
        lavalink_port=lavalink_port,
        lavalink_password=lavalink_password,
        lavalink_secured=lavalink_secured,
        auto_join_track_url=auto_join_track_url,
        auto_join_channel_id=auto_join_channel_id,
        auto_join_user_id=auto_join_user_id,
        runtime_config_path=os.getenv("RUNTIME_CONFIG_PATH", "/app/data/runtime-config.json").strip()
        or "/app/data/runtime-config.json",
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
    )

    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    return settings
