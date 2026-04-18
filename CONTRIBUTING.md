# Contributing

Thanks for helping improve Flash105.

## Development Notes

- The bot runtime is in `musicbot/`
- Docker support is defined in `Dockerfile` and `docker-compose.yml`
- Unraid materials live in `unraid/`

## Local Workflow

1. Copy `.env.example` to `.env`
2. Fill in your Discord bot token
3. Start the stack:

```bash
docker compose up --build -d
docker compose logs -f
```

## Pull Requests

- Keep changes focused and easy to review
- Update docs when behavior or setup changes
- If you change Unraid behavior, update both `README.md` and `unraid/`
- Prefer practical fixes over large refactors unless there is a clear benefit

## Publishing Images

The public image is `shuaturner/flash105:latest`.

GitHub Actions can publish it automatically when these repository secrets are configured:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

Manual publishing is still possible for maintainers:

```bash
docker build -t shuaturner/flash105:latest .
docker push shuaturner/flash105:latest
```

## Bug Reports

When reporting a bug, include:

- what command you ran
- what you expected
- what happened instead
- relevant bot or Lavalink logs
- whether the issue is local Docker, Docker Hub, or Unraid specific
