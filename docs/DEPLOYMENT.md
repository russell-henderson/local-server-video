# Deployment

## Local Flask Run

```powershell
python main.py
```

Default host/port comes from `config.py` and `LVS_*` environment overrides.

## Docker Compose Run

```powershell
docker compose up --build
```

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
