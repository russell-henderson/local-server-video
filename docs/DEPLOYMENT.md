# Deployment

Verified LAN access on the current workspace host:

- `http://192.168.4.96:5000/`
- `http://192.168.4.96:8000/`

## Local Flask Run

```powershell
python main.py
```

Default host/port comes from `config.py` and `LVS_*` environment overrides.

## Docker Compose Run

```powershell
docker compose up --build
```

`docker-compose.yml` publishes the Flask container on `5000:5000` and the nginx proxy on `8000:80`, so the service is not localhost-only.

## Runtime Data Paths

- Host:
  - `data/video_metadata.db`
  - `data/video_search.db`
- Container:
  - `/app/data/video_metadata.db`
  - `/app/data/video_search.db`

`docker-compose.yml` sets `LVS_DB_PATH=data/video_metadata.db` for app runtime consistency.

## Baseline Safety Step Before Refactor Work

Create a snapshot of DB/JSON artifacts:

```powershell
python scripts/import_sidecar_tags_to_db.py
```

And keep the generated baseline record in `docs/BASELINE_FREEZE.md`.
