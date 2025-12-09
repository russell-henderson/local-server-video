# Performance Monitoring & Health Checks

## Request Timing Logs
- Implemented via Flask `before_request`/`after_request` hooks in `main.py`.
- Uses `time.perf_counter()` for wall-clock accuracy.
- Controlled by `ServerConfig.enable_perf_log` (env `LVS_ENABLE_PERF_LOG`, default `true`).
- Example log line:
  ```
  [PERF] ts=2025-11-24T12:34:56 method=GET path=/watch/foo.mp4 status=200 duration_ms=42.17
  ```
- Rough guidance: `<50ms` fully cached; `50–150ms` light work; `>200ms` investigate IO/DB/thumbnail work.

## HTTP Smoke Load Check
- Script: `scripts/http_smoke_load_check.py`
- Behavior: probes a single path (default `/`) against `LVS_SMOKE_BASE_URL` (default `http://127.0.0.1:5000`) a fixed number of times (default 10).
- CLI args:
  - `--iterations` (default 10)
  - `--path` (default `/`)
- Fixed thresholds: fail if any non-2xx response, or `avg_ms > 200` or `p95_ms > 400`.
- Example:
  ```bash
  LVS_SMOKE_BASE_URL=http://127.0.0.1:5000 python scripts/http_smoke_load_check.py --iterations 10 --path /tags
  ```

## CI Workflow
Workflow: `.github/workflows/health_and_perf.yml`

Steps:
1. Install dependencies.
2. Run `python scripts/db_health_check.py`.
3. Start the Flask app (`python main.py`), wait for it to bind.
4. Run `python scripts/http_smoke_load_check.py --iterations 10` (defaults to `/`).
5. Upload server logs and stop the app (even on failure).

Interpreting failures:
- **db_health_check.py**: investigate missing tables/indexes or bad row counts.
- **http_smoke_load_check.py**: check the per-request lines and summary stats; inspect `server.log` artifact.
- Reproduce locally with the same commands to debug.
