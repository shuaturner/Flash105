# Community Applications Checklist

Use this as the minimum checklist before trying to publish on Unraid Community Applications.

## Required

- Host the template XML files on GitHub.
- Create a dedicated Unraid forum support thread.
- Keep installation and troubleshooting docs up to date.
- Be ready to maintain the templates and respond to support requests.

## Recommended Structure

- Publish `unraid/templates/discord-music-bot.xml`
- Publish `unraid/templates/lavalink.xml`
- Reference the Docker Hub bot image: `shuaturner/flash105:latest`
- Reference the Lavalink image: `ghcr.io/lavalink-devs/lavalink:4-alpine`

## Suggested Submission Notes

- The bot template depends on a Lavalink container.
- The Lavalink container should keep the container name `lavalink`, or the user must change `LAVALINK_HOST`.
- The Lavalink template requires:
  - `/mnt/user/appdata/discord-music-bot/lavalink/application.yml`
  - `/mnt/user/appdata/discord-music-bot/lavalink/plugins`

## Helpful Links

- Unraid Community Applications docs:
  - https://docs.unraid.net/unraid-os/using-unraid-to/run-docker-containers/community-applications/
- Docker template XML schema thread:
  - https://forums.unraid.net/topic/38619-docker-template-xml-schema/
