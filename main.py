"""Thin bootstrap entrypoint for Local Video Server."""

from backend.app.factory import create_app
from backend.app import legacy_runtime as legacy
from cache_manager import cache
from config import get_config

app = create_app()
startup_tasks = legacy.startup_tasks


if __name__ == "__main__":
    print("[STARTUP] Starting Local Video Server (factory bootstrap)...")
    backend = "Database" if cache.use_database else "Unavailable"
    print(f"[STARTUP] Backend: {backend}")

    with app.app_context():
        startup_tasks()

    config = get_config()
    app.run(host=config.host, port=config.port, debug=config.debug, threaded=True)
