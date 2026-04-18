from __future__ import annotations

from musicbot.bot import MusicBot
from musicbot.config import load_settings


def main() -> None:
    settings = load_settings()
    bot = MusicBot(settings)
    bot.run(settings.discord_token, log_handler=None)


if __name__ == "__main__":
    main()
