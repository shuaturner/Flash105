# Discord Music Bot

A Docker-ready Discord music bot built around `discord.py`, Lavalink v4, and the official Lavalink YouTube plugin.

It supports:

- YouTube search queries
- direct YouTube URLs
- slash-command playback in your Discord server
- a two-container deployment that runs well locally or on Unraid

## Commands

- `/play query:<song or url>`
- `/skip`
- `/pause`
- `/resume`
- `/stop`
- `/leave`
- `/queue`
- `/nowplaying`

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

Run the published image with compose:

```bash
BOT_IMAGE=shuaturner/flash105:latest docker compose up -d
```

## Unraid Notes

For Unraid, keep the same two-service layout:

- one container from `shuaturner/flash105:latest`
- one container from `ghcr.io/lavalink-devs/lavalink:4-alpine`

Recommended persistent paths:

- map your bot `.env` file or set the environment variables directly in Unraid
- mount `application.yml` into `/opt/Lavalink/application.yml`
- mount a persistent plugins folder into `/opt/Lavalink/plugins`

The `plugins` mount lets Lavalink keep the downloaded YouTube plugin between restarts.

An example Unraid-oriented compose file is included at `unraid/docker-compose.unraid.yml`.
An example bot env file is included at `unraid/bot.env.example`.
Starter CA template XML files are included at `unraid/templates/`.
There is also a short CA publishing checklist at `unraid/ca-submission-checklist.md`.
There is a starter Unraid support-thread post at `unraid/support-thread-draft.md`.

Suggested Unraid appdata layout:

```text
/mnt/user/appdata/discord-music-bot/
  bot/
    .env
  lavalink/
    application.yml
    plugins/
```

### Unraid Setup Steps

1. On Unraid, create these folders:

```bash
mkdir -p /mnt/user/appdata/discord-music-bot/bot
mkdir -p /mnt/user/appdata/discord-music-bot/lavalink/plugins
```

2. Copy these files to Unraid:

- `application.yml` -> `/mnt/user/appdata/discord-music-bot/lavalink/application.yml`
- `unraid/bot.env.example` -> `/mnt/user/appdata/discord-music-bot/bot/.env`
- `unraid/docker-compose.unraid.yml` -> anywhere convenient, for example `/mnt/user/appdata/discord-music-bot/docker-compose.yml`

3. Edit `/mnt/user/appdata/discord-music-bot/bot/.env` and set:

- `DISCORD_TOKEN`
- optionally `DISCORD_SERVER_ID`

4. In the Unraid terminal, start the stack:

```bash
cd /mnt/user/appdata/discord-music-bot
docker compose -f docker-compose.yml up -d
```

5. Check logs:

```bash
docker compose -f /mnt/user/appdata/discord-music-bot/docker-compose.yml logs -f
```

### Updating On Unraid

When a new bot image is published:

```bash
docker compose -f /mnt/user/appdata/discord-music-bot/docker-compose.yml pull
docker compose -f /mnt/user/appdata/discord-music-bot/docker-compose.yml up -d
```

## GitHub Automation

The repository includes a GitHub Actions workflow at `.github/workflows/docker-publish.yml`.

To use it, add these repository secrets:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

After that, pushes to `main` and version tags can automatically publish updated Docker images.

## Project Notes

- Lavalink handles the actual audio sending and YouTube source loading.
- `application.yml` disables Lavalink's deprecated built-in YouTube source and enables the maintained plugin instead.
- If you set `DISCORD_SERVER_ID`, slash commands sync directly to that server instead of waiting on slower global propagation.
