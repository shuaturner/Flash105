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
- Reference the bundled Lavalink image: `shuaturner/flash105-lavalink:latest`

## Suggested Submission Notes

- The bot template depends on a Lavalink container.
- If installed as separate templates, both containers should be placed on the same user-defined Docker network so the hostname `lavalink` resolves.
- The Lavalink container should keep the container name `lavalink`, or the user must change `LAVALINK_HOST`.
- The bundled Lavalink image includes `application.yml` and the YouTube plugin jar, so the template does not need appdata mounts.

## Helpful Links

- Unraid Community Applications docs:
  - https://docs.unraid.net/unraid-os/using-unraid-to/run-docker-containers/community-applications/
- Docker template XML schema thread:
  - https://forums.unraid.net/topic/38619-docker-template-xml-schema/
