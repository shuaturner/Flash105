# Unraid Support Thread Draft

## Flash105

Flash105 is a Discord music bot built with `discord.py` and Lavalink v4.

It supports:

- slash-command playback
- YouTube search and direct YouTube URLs
- Docker deployment
- Unraid deployment

### Containers

This setup uses two containers:

- `shuaturner/flash105:latest`
- `ghcr.io/lavalink-devs/lavalink:4-alpine`

### Requirements

- a Discord bot token
- a Lavalink container
- `application.yml` mounted into Lavalink
- a persistent Lavalink plugins folder

### Useful Links

- Docker Hub: https://hub.docker.com/r/shuaturner/flash105
- GitHub: https://github.com/shuaturner/Flash105

### Common Setup Notes

- The bot container expects the Lavalink hostname to be `lavalink` by default.
- If you rename the Lavalink container, set `LAVALINK_HOST` to match.
- The Lavalink plugins folder should be persistent so the YouTube plugin survives restarts.

### If You Need Help

Please include:

- your Unraid version
- whether you used compose or manual container setup
- your bot logs
- your Lavalink logs
- whether the issue is startup, voice join, or playback
