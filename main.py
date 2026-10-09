"""Thin bootstrap entrypoint for Local Video Server."""

import argparse

from backend.app.factory import create_app
from backend.app import legacy_runtime as legacy
from cache_manager import cache
from config import get_config

app = create_app()
startup_tasks = legacy.startup_tasks


def _parse_args() -> argparse.Namespace:
    """Parse local-run overrides without changing the project configuration."""
    config = get_config()
    parser = argparse.ArgumentParser(description="Run the Local Video Server with Flask.")
    parser.add_argument(
        "--host",
        default=config.host,
        help=f"Interface to bind (default: {config.host})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=config.port,
        help=f"HTTP port to bind (default: {config.port})",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable Flask debug mode for local development.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    print("[STARTUP] Starting Local Video Server (factory bootstrap)...")
    backend = "Database" if cache.use_database else "Unavailable"
    print(f"[STARTUP] Backend: {backend}")

    with app.app_context():
        startup_tasks()

    args = _parse_args()
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)
