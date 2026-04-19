# Discord Music Bot

A Docker-ready Discord music bot built around `discord.py`, Lavalink v4, and the official Lavalink YouTube plugin.

It supports:

- YouTube search queries
- direct YouTube URLs
- slash-command playback in your Discord server
- a two-container deployment that runs well locally or on Unraid

## Commands

- `/play query:<song or url>`
- `/sendgps query:<song or url>` (This is just for Andy)
- `/skip`
- `/pause`
- `/resume`
- `/stop`
- `/leave`
- `/queue`
- `/nowplaying`

`/play`, `/sendgps`, and `/nowplaying` show Discord button controls for pause, resume, skip, queue, and leave. Public playback messages are cleaned up when playback is stopped, the bot leaves, or the voice channel becomes empty.

## Discord Setup

In the Discord developer portal:

- enable a bot user
- invite with the `bot` and `applications.commands` scopes
- grant `View Channels`, `Connect`, and `Speak`

Privileged intents are not required for this project. The bot only uses `Guilds` and `Voice States`.

## Environment

Copy `.env.example` to `.env` and fill in:

- `DISCORD_TOKEN`: required
- `DISCORD_SERVER_ID`: optional but recommended for faster slash-command sync during setup
- `LAVALINK_HOST`: optional, defaults to `lavalink`
- `LAVALINK_PORT`: optional, defaults to `2333`
- `LAVALINK_PASSWORD`: optional, defaults to `youshallnotpass`
- `LAVALINK_SECURED`: optional, defaults to `false`
- `LOG_LEVEL`: optional, defaults to `INFO`

## Run With Docker

```bash
docker compose up --build -d
docker compose logs -f
```

## Run With Published Image

The bot image is published as `shuaturner/flash105:latest`.
The preconfigured Lavalink companion image is published as `shuaturner/flash105-lavalink:latest`.

Run the published image with compose:

```bash
BOT_IMAGE=shuaturner/flash105:latest LAVALINK_IMAGE=shuaturner/flash105-lavalink:latest docker compose up -d
```

## Unraid Notes

For Unraid, use the included templates from `unraid/templates/`:

- `discord-music-bot.xml` for `shuaturner/flash105:latest`
- `lavalink.xml` for `shuaturner/flash105-lavalink:latest`

Install the Lavalink container first, then install the bot container. Put both containers on the same Docker network so the bot can reach Lavalink at the hostname `lavalink`.

In the bot template, set:

- `DISCORD_TOKEN`
- `DISCORD_SERVER_ID`, optional but recommended for faster slash-command sync

The bundled Lavalink image already includes `application.yml` and the YouTube plugin jar, so Unraid users do not need to copy a Lavalink config file or maintain a writable plugin folder manually.

Extra Unraid publishing materials are included in `unraid/ca-submission-checklist.md` and `unraid/support-thread-draft.md`.

## GitHub Automation

The repository includes a GitHub Actions workflow at `.github/workflows/docker-publish.yml`.

To use it, add these repository secrets in GitHub under `Settings` > `Secrets and variables` > `Actions` > `Repository secrets`:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN` - a Docker Hub access token with permission to publish `shuaturner/flash105`

After that, pushes to `main` and version tags can automatically publish updated Docker images.

## Project Notes

- Lavalink handles the actual audio sending and YouTube source loading.
- `application.yml` disables Lavalink's deprecated built-in YouTube source and enables the maintained plugin instead.
- If you set `DISCORD_SERVER_ID`, slash commands sync directly to that server instead of waiting on slower global propagation.
