# Performance Monitoring & Health Checks

## Request Timing Logs

- Implemented via Flask `before_request`/`after_request` hooks in `main.py`.
- Uses `time.perf_counter()` for wall-clock accuracy.
- Controlled by `ServerConfig.enable_perf_log` (env var `LVS_ENABLE_PERF_LOG`, default `true`).

### Example log line

```
[PERF] ts=2025-11-24T12:34:56 method=GET path=/watch/foo.mp4 status=200 duration_ms=42.17
```

### Interpreting durations

- **< 50 ms**: fully cached route; healthy for local/staging.
- **50–150 ms**: includes DB work or light cache misses.
- **> 200 ms**: investigate DB queries, filesystem IO, or thumbnail generation.

Disable logging by setting `LVS_ENABLE_PERF_LOG=false` (or editing `config.json`) and restarting the server.

## HTTP Smoke Load Check

- Script: `scripts/http_smoke_load_check.py`
- Defaults: hits `/`, `/watch/<video>`, `/tags` 30 times each (auto-detects a watch link).
- Configure base URL via `--base-url` or `LVS_SMOKE_BASE_URL`.
- Thresholds (overridable):
  - Average latency ≤ 200 ms
  - P95 latency ≤ 400 ms
- Exit code 1 if:
  - Any request returned non-2xx
  - Average or p95 exceeds the thresholds

Example:
```bash
python scripts/http_smoke_load_check.py --base-url http://127.0.0.1:5000 --iterations 20
```

## CI Workflow

Workflow: `.github/workflows/health_and_perf.yml`

Steps:
1. Install dependencies.
2. Run `python scripts/db_health_check.py`.
3. Start the Flask app (`python main.py`), wait for it to bind.
4. Run `python scripts/http_smoke_load_check.py --iterations 10`.
5. Upload server logs and stop the app (even on failure).

Interpreting failures:
- **db_health_check.py**: Investigate missing tables/indexes or bad row counts.
- **http_smoke_load_check.py**: Look at the printed stats and `server.log` artifact.
- Reproduce locally with the same commands to debug.

