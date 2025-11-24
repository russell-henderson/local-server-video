#!/usr/bin/env python3
"""
HTTP smoke/load check for Local Video Server.

Usage:
    python scripts/http_smoke_load_check.py --base-url http://127.0.0.1:5000

Environment:
    LVS_SMOKE_BASE_URL can override the default base URL.

What it does:
    - Hits /, /watch/<video>, and /tags repeatedly (default 30 requests each).
    - Records min/avg/p95/max latency and counts non-2xx responses.
    - Exits with code 1 if any endpoint fails or exceeds latency thresholds.

Notes:
    - Pass --watch-path if auto-discovery cannot find a /watch/<video> link.
    - Adjust --iterations/--max-avg-ms/--max-p95-ms as needed.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from statistics import mean
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests

DEFAULT_BASE_URL = os.environ.get("LVS_SMOKE_BASE_URL", "http://localhost:5000")
DEFAULT_ITERATIONS = 30
MAX_AVG_MS = float(os.environ.get("LVS_SMOKE_MAX_AVG_MS", 200))
MAX_P95_MS = float(os.environ.get("LVS_SMOKE_MAX_P95_MS", 400))


def percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    k = max(0, min(len(ordered) - 1, int((pct / 100.0) * len(ordered))))
    return ordered[k]


def discover_watch_path(session: requests.Session, base_url: str) -> Optional[str]:
    """Fetch home page once to locate a watch link."""
    try:
        resp = session.get(urljoin(base_url, "/"), timeout=10)
        resp.raise_for_status()
    except requests.RequestException:
        return None

    match = re.search(r'href="(/watch/[^"]+)"', resp.text)
    if match:
        return match.group(1)
    return None


def run_endpoint(
    session: requests.Session,
    base_url: str,
    path: str,
    iterations: int,
) -> Dict[str, float]:
    url = urljoin(base_url, path)
    durations: List[float] = []
    errors = 0

    for _ in range(iterations):
        start = time.perf_counter()
        try:
            resp = session.get(url, timeout=10)
            ok = 200 <= resp.status_code < 300
        except requests.RequestException:
            ok = False
        duration = (time.perf_counter() - start) * 1000.0
        durations.append(duration)
        if not ok:
            errors += 1

    stats = {
        "count": len(durations),
        "min_ms": min(durations) if durations else 0.0,
        "avg_ms": mean(durations) if durations else 0.0,
        "p95_ms": percentile(durations, 95),
        "max_ms": max(durations) if durations else 0.0,
        "status_ok": errors == 0,
        "errors": errors,
    }
    return stats


def format_stats(name: str, path: str, stats: Dict[str, float]) -> str:
    return (
        f"Endpoint: {name} ({path})\n"
        f"  requests: {stats['count']}\n"
        f"  status_ok: {stats['status_ok']} (errors={int(stats['errors'])})\n"
        f"  min_ms: {stats['min_ms']:.1f}\n"
        f"  avg_ms: {stats['avg_ms']:.1f}\n"
        f"  p95_ms: {stats['p95_ms']:.1f}\n"
        f"  max_ms: {stats['max_ms']:.1f}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="HTTP smoke/load check.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base URL to test.")
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS)
    parser.add_argument("--watch-path", help="Override /watch path to probe.")
    parser.add_argument("--tags-path", default="/tags", help="Tags path to probe.")
    parser.add_argument("--max-avg-ms", type=float, default=MAX_AVG_MS)
    parser.add_argument("--max-p95-ms", type=float, default=MAX_P95_MS)
    args = parser.parse_args()

    session = requests.Session()
    watch_path = args.watch_path
    if not watch_path:
        watch_path = discover_watch_path(session, args.base_url)
        if watch_path:
            print(f"[INFO] Discovered watch path: {watch_path}")
        else:
            print("[WARN] Could not auto-detect a /watch/<video> path; skipping watch endpoint.")

    endpoints = [
        {"name": "home", "path": "/", "iterations": args.iterations},
        {"name": "watch", "path": watch_path, "iterations": args.iterations} if watch_path else None,
        {"name": "tags", "path": args.tags_path, "iterations": args.iterations},
    ]
    endpoints = [ep for ep in endpoints if ep]

    overall_ok = True
    summaries: List[str] = []

    for ep in endpoints:
        stats = run_endpoint(session, args.base_url, ep["path"], ep["iterations"])
        summaries.append(format_stats(ep["name"], ep["path"], stats))
        if (
            not stats["status_ok"]
            or stats["avg_ms"] > args.max_avg_ms
            or stats["p95_ms"] > args.max_p95_ms
        ):
            overall_ok = False

    print("\n".join(summaries))

    if not overall_ok:
        print(
            f"[FAIL] Smoke check failed (avg>{args.max_avg_ms}ms or p95>{args.max_p95_ms}ms or non-2xx responses)."
        )
        return 1

    print("[OK] Smoke check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

