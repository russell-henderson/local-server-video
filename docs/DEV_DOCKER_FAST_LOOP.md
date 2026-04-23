# Docker Fast Dev Loop

Use this workflow to apply server/template/static code changes without full image rebuilds.

## What Was Added

- `docker-compose.override.yml` bind-mounts the project root into `/app`.
- `video-server` runs with Flask auto-reload (`flask run --reload`).
- `LVS_DEBUG=true` is set for development behavior.

## Start Fast Loop

```powershell
docker compose up -d video-server
```

This starts `video-server` using the base compose file plus the override automatically.

## Makefile Shortcuts

You can use these convenience commands:

```powershell
make dev-up
make dev-logs
make dev-down
```

## How Changes Apply

- Python (`main.py`, backend modules): auto-reload on save.
- Templates (`templates/*.html`): reflected on refresh (hard refresh if browser caches aggressively).
- Static served by Flask (`/static/*` on `:5000`): reflected on refresh.
- Static via nginx (`:8080`) already uses a bind mount from base compose and updates without rebuild.

## When Rebuild Is Still Required

Rebuild only when dependencies or image layers change:

- `requirements.txt` changed
- `Dockerfile` changed
- system packages changed

Use targeted rebuild:

```powershell
docker compose build video-server
docker compose up -d video-server
```

## Optional One-Off Hotfix (No Override)

If you ever need to patch a running container quickly:

```powershell
docker compose cp main.py video-server:/app/main.py
docker compose restart video-server
```
