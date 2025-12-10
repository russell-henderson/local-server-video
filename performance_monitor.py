"""
Performance Monitoring and Testing Utilities
"""
from __future__ import annotations

import functools
import os
import socket
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psutil

from backend.app.admin.performance import DEFAULT_WINDOW_SECONDS, get_metrics

# Allowed windows for aggregation
ALLOWED_WINDOWS = {300, 900, 3600}
SNAPSHOT_TTL_SECONDS = 2.0


@dataclass
class PerformanceMetric:
    """Performance metric data class."""

    name: str
    duration: float
    memory_before: float
    memory_after: float
    timestamp: float


class PerformanceMonitor:
    """Performance monitoring singleton bridging diagnostic and admin metrics."""

    _instance: Optional["PerformanceMonitor"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(PerformanceMonitor, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.metrics: List[PerformanceMetric] = []
            # Legacy stats retained for human readable report output
            self.route_stats: Dict[str, List[float]] = {}
            self.cache_stats = {
                "hits": 0,
                "misses": 0,
                "total_requests": 0,
            }
            self._initialized = True

    # --- recorders -------------------------------------------------

    def record_metric(self, metric: PerformanceMetric) -> None:
        """Record a performance metric and keep history bounded."""
        self.metrics.append(metric)
        if len(self.metrics) > 1000:
            self.metrics = self.metrics[-1000:]

    def record_route_time(
        self,
        route: str,
        duration: float,
        status_code: int = 200,
        *,
        endpoint: Optional[str] = None,
        path: Optional[str] = None,
        method: Optional[str] = None,
        remote_addr: Optional[str] = None,
    ) -> None:
        """Record route execution time and forward to admin metrics."""
        self.route_stats.setdefault(route, []).append(duration)
        if len(self.route_stats[route]) > 100:
            self.route_stats[route] = self.route_stats[route][-100:]

        try:
            get_metrics().record_endpoint_latency(
                route,
                duration,
                status_code=status_code,
                method=method,
                path=path,
                endpoint_name=endpoint,
                remote_addr=remote_addr,
            )
        except Exception:
            # Do not interrupt request flow if metrics recording fails
            pass

    def record_cache_hit(self) -> None:
        """Record cache hit."""
        self.cache_stats["hits"] += 1
        self.cache_stats["total_requests"] += 1
        try:
            get_metrics().record_cache_hit()
        except Exception:
            pass

    def record_cache_miss(self) -> None:
        """Record cache miss."""
        self.cache_stats["misses"] += 1
        self.cache_stats["total_requests"] += 1
        try:
            get_metrics().record_cache_miss()
        except Exception:
            pass

    # --- readers ---------------------------------------------------

    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate percentage."""
        total = self.cache_stats["total_requests"]
        if total == 0:
            return 0.0
        return (self.cache_stats["hits"] / total) * 100

    def get_route_stats(self) -> Dict[str, Dict[str, float]]:
        """Get aggregated route statistics."""
        stats: Dict[str, Dict[str, float]] = {}
        for route, times in self.route_stats.items():
            if times:
                stats[route] = {
                    "avg_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times),
                    "request_count": len(times),
                }
        return stats

    def get_recent_metrics(self, limit: int = 10) -> List[PerformanceMetric]:
        """Get recent performance metrics."""
        return self.metrics[-limit:]

    def reset_stats(self) -> None:
        """Reset all statistics."""
        self.metrics.clear()
        self.route_stats.clear()
        self.cache_stats = {"hits": 0, "misses": 0, "total_requests": 0}


# Global monitor instance
monitor = PerformanceMonitor()


def performance_monitor(func_name: Optional[str] = None):
    """Decorator to monitor function performance."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = func_name or f"{func.__module__}.{func.__name__}"
            process = psutil.Process(os.getpid())
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            start_time = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.time() - start_time
                memory_after = process.memory_info().rss / 1024 / 1024  # MB

                monitor.record_metric(
                    PerformanceMetric(
                        name=name,
                        duration=duration,
                        memory_before=memory_before,
                        memory_after=memory_after,
                        timestamp=start_time,
                    )
                )

                # Avoid double counting when Flask hooks already capture routes
                try:
                    from flask import has_request_context
                except Exception:
                    has_request_context = None  # type: ignore

                should_record_route = not (has_request_context and has_request_context())
                if should_record_route and (
                    "route" in name.lower()
                    or any(
                        indicator in name.lower()
                        for indicator in ["index", "watch", "stream", "api"]
                    )
                ):
                    monitor.record_route_time(name, duration)

        return wrapper

    return decorator


def flask_route_monitor(app):
    """Add performance monitoring to Flask routes."""

    @app.before_request
    def before_request():
        """Record request start time."""
        from flask import g

        g.start_time = time.time()

    @app.after_request
    def after_request(response):
        """Record request performance."""
        from flask import g, request

        if hasattr(g, "start_time"):
            duration = time.time() - g.start_time
            route_rule = getattr(request, "url_rule", None)
            path = route_rule.rule if route_rule else request.path
            route_name = f"{request.method} {path}"
            monitor.record_route_time(
                route_name,
                duration,
                status_code=getattr(response, "status_code", 200),
                endpoint=request.endpoint or "unknown",
                path=path,
                method=request.method,
                remote_addr=getattr(request, "remote_addr", None),
            )

        return response

    return app


# --- admin snapshot helpers --------------------------------------------------

_SNAPSHOT_CACHE: Dict[Tuple[int, bool, bool], Tuple[float, Dict[str, Any]]] = {}


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _validate_window_seconds(window_seconds: Optional[int]) -> int:
    if window_seconds is None:
        return DEFAULT_WINDOW_SECONDS
    if window_seconds not in ALLOWED_WINDOWS:
        raise ValueError(f"window_seconds must be one of {sorted(ALLOWED_WINDOWS)}")
    return window_seconds


def _route_status(p95_ms: float, error_rate: float) -> str:
    if error_rate >= 0.05 or p95_ms > 500:
        return "poor"
    if error_rate >= 0.02 or p95_ms > 250:
        return "warning"
    if p95_ms == 0:
        return "unknown"
    return "good"


def _overall_status(
    global_metrics: Dict[str, Any],
    cache_metrics: Dict[str, Any],
    workers: Dict[str, Any],
) -> Dict[str, Any]:
    status = "good"
    issues: List[str] = []

    if global_metrics.get("p95_latency_ms", 0) > 500 or global_metrics.get(
        "error_rate", 0
    ) > 0.05:
        status = "critical"
        issues.append("High global latency or error rate")
    elif global_metrics.get("p95_latency_ms", 0) > 250 or global_metrics.get(
        "error_rate", 0
    ) > 0.02:
        status = "warning"
        issues.append("Elevated latency or error rate")

    cache_status = cache_metrics.get("status")
    if cache_status in ("full", "warning") and status == "good":
        status = "warning"
        issues.append("Cache usage high")

    worker_status = workers.get("status")
    if worker_status in ("error", "warning") and status == "good":
        status = "warning"
        issues.append("Workers reporting warnings")

    return {"overall": status, "issues": issues}


def _cache_metrics() -> Dict[str, Any]:
    preview_dir = Path("static") / "thumbnails"
    total_bytes = 0
    file_count = 0
    if preview_dir.exists():
        for path in preview_dir.rglob("*"):
            if path.is_file():
                file_count += 1
                try:
                    total_bytes += path.stat().st_size
                except OSError:
                    continue

    limit_bytes = 50 * 1024 * 1024 * 1024  # 50 GB default upper bound
    usage_ratio = (total_bytes / limit_bytes) if limit_bytes else 0.0
    status = "good"
    if usage_ratio >= 0.95:
        status = "full"
    elif usage_ratio >= 0.8:
        status = "warning"

    return {
        "preview_cache_bytes": int(total_bytes),
        "preview_cache_limit_bytes": int(limit_bytes),
        "preview_cache_usage_ratio": float(usage_ratio),
        "preview_cache_items": file_count,
        "last_refresh_at": None,
        "status": status,
    }


def _global_metrics(window_seconds: int) -> Dict[str, Any]:
    metrics = get_metrics()
    cutoff = time.time() - window_seconds
    with metrics.lock:
        samples = [s for s in metrics.global_samples if s["timestamp"] >= cutoff]
        latencies = [s["duration_ms"] for s in samples]
        error_count = len([s for s in samples if s.get("status_code", 200) >= 500])
        request_count = len(samples)
        p50, p95, p99 = metrics._get_latency_percentiles(latencies)
        error_rate = (error_count / request_count) if request_count else 0.0

    return {
        "request_count": request_count,
        "error_count": error_count,
        "error_rate": error_rate,
        "p50_latency_ms": p50,
        "p95_latency_ms": p95,
        "p99_latency_ms": p99,
    }


def _ratings_metrics(window_seconds: int) -> Optional[Dict[str, Any]]:
    metrics = get_metrics()
    cutoff = time.time() - window_seconds
    with metrics.lock:
        latencies = []
        error_count = 0
        request_count = 0
        for key, dq in metrics.route_samples.items():
            if not (key.startswith("POST") and "/api/ratings" in key):
                continue
            for sample in dq:
                if sample["timestamp"] < cutoff:
                    continue
                request_count += 1
                latencies.append(sample["duration_ms"])
                if sample.get("status_code", 200) >= 500:
                    error_count += 1

        if not request_count:
            return None

        p50, p95, p99 = metrics._get_latency_percentiles(latencies)
        error_rate = error_count / request_count if request_count else 0.0
        status = _route_status(p95, error_rate)

    return {
        "path": "/api/ratings",
        "method": "POST",
        "name": "ratings",
        "request_count": request_count,
        "error_count": error_count,
        "error_rate": error_rate,
        "p50_latency_ms": p50,
        "p95_latency_ms": p95,
        "p99_latency_ms": p99,
        "status": status,
    }


def _database_metrics() -> Dict[str, Any]:
    metrics = get_metrics()
    with metrics.lock:
        samples = list(metrics.db_queries_per_request)
        total_queries = sum(samples)
        count = len(samples)
        avg_per_request = (total_queries / count) if count else 0
        max_per_request = max(samples) if samples else 0
    return {
        "total_queries": total_queries,
        "avg_per_request": avg_per_request,
        "max_per_request": max_per_request,
        "count": count,
    }


def get_route_metrics(
    window_seconds: int = DEFAULT_WINDOW_SECONDS,
    sort_by: str = "p95_latency_ms",
    order: str = "desc",
    limit: int = 100,
) -> Dict[str, Any]:
    """Return sorted route metrics payload."""
    window_seconds = _validate_window_seconds(window_seconds)
    sort_key_map = {
        "p95_latency_ms": "p95_latency_ms",
        "error_rate": "error_rate",
        "request_count": "request_count",
        "path": "path",
    }
    if sort_by not in sort_key_map:
        raise ValueError(
            "sort_by must be one of ['p95_latency_ms', 'error_rate', 'request_count', 'path']"
        )
    if order not in ("asc", "desc"):
        raise ValueError("order must be 'asc' or 'desc'")

    metrics = get_metrics()
    cutoff = time.time() - window_seconds
    routes: List[Dict[str, Any]] = []

    with metrics.lock:
        for key, dq in metrics.route_samples.items():
            samples = [s for s in dq if s["timestamp"] >= cutoff]
            if not samples:
                continue

            latencies = [s["duration_ms"] for s in samples]
            p50, p95, p99 = metrics._get_latency_percentiles(latencies)
            request_count = len(samples)
            error_count = len([s for s in samples if s.get("status_code", 200) >= 500])
            error_rate = error_count / request_count if request_count else 0.0
            method = samples[-1].get("method") or key.split(" ")[0]
            path = samples[-1].get("path") or (key.split(" ", 1)[1] if " " in key else key)
            endpoint_name = samples[-1].get("endpoint") or key

            routes.append(
                {
                    "path": path,
                    "method": method,
                    "name": endpoint_name,
                    "request_count": request_count,
                    "error_count": error_count,
                    "error_rate": error_rate,
                    "p50_latency_ms": p50,
                    "p95_latency_ms": p95,
                    "p99_latency_ms": p99,
                    "status": _route_status(p95, error_rate),
                }
            )

    reverse = order == "desc"
    routes.sort(key=lambda r: r[sort_key_map[sort_by]], reverse=reverse)
    routes = routes[: max(1, limit)]

    return {
        "generated_at": _utcnow_iso(),
        "window_seconds": window_seconds,
        "routes": routes,
    }


def get_worker_metrics() -> Dict[str, Any]:
    """Return worker/queue metrics. Workers are currently disabled."""
    return {
        "generated_at": _utcnow_iso(),
        "worker_count": 0,
        "workers": [],
        "queues": [],
        "status": "disabled",
    }


def get_active_streams(window_seconds: int = 300, limit: int = 10) -> Dict[str, Any]:
    """Return recently active watch/video requests with remote addresses."""
    metrics = get_metrics()
    cutoff = time.time() - window_seconds
    streams: List[Dict[str, Any]] = []
    with metrics.lock:
        for key, dq in metrics.route_samples.items():
            samples = [s for s in dq if s.get("timestamp", 0) >= cutoff]
            if not samples:
                continue
            last = samples[-1]
            path = last.get("path") or (key.split(" ", 1)[1] if " " in key else key)
            if not path or ("/watch" not in path and "/video" not in path):
                continue
            elapsed = max(0, time.time() - last.get("timestamp", 0))
            streams.append(
                {
                    "path": path,
                    "method": last.get("method") or key.split(" ")[0],
                    "endpoint": last.get("endpoint") or key,
                    "remote_addr": last.get("remote_addr"),
                    "last_seen_seconds_ago": elapsed,
                }
            )
    streams.sort(key=lambda s: s["last_seen_seconds_ago"])
    return {
        "generated_at": _utcnow_iso(),
        "active_count": min(len(streams), limit),
        "streams": streams[:limit],
    }


def get_performance_snapshot(
    window_seconds: int = DEFAULT_WINDOW_SECONDS,
    include_routes: bool = False,
    include_workers: bool = True,
) -> Dict[str, Any]:
    """Return PerformanceSnapshot payload for admin dashboard."""
    window_seconds = _validate_window_seconds(window_seconds)
    cache_key = (window_seconds, include_routes, include_workers)
    now = time.time()
    cached = _SNAPSHOT_CACHE.get(cache_key)
    if cached and (now - cached[0]) < SNAPSHOT_TTL_SECONDS:
        return cached[1]

    cache_metrics = _cache_metrics()
    global_metrics = _global_metrics(window_seconds)
    ratings_metrics = _ratings_metrics(window_seconds)
    database_metrics = _database_metrics()
    workers = get_worker_metrics() if include_workers else {
        "worker_count": 0,
        "workers": [],
        "queues": [],
        "status": "disabled",
    }

    snapshot: Dict[str, Any] = {
        "generated_at": _utcnow_iso(),
        "window_seconds": window_seconds,
        "server": {
            "version": os.getenv("LVS_VERSION", "dev"),
            "environment": os.getenv("FLASK_ENV", "development"),
            "uptime_seconds": get_metrics().get_uptime_seconds(),
            "hostname": socket.gethostname(),
        },
        "global": global_metrics,
        "ratings": ratings_metrics,
        "database": database_metrics,
        "cache": cache_metrics,
        "workers": workers,
        "status": _overall_status(global_metrics, cache_metrics, workers),
        "routes": None,
    }

    if include_routes:
        snapshot["routes"] = get_route_metrics(
            window_seconds, "p95_latency_ms", "desc", 100
        )["routes"]

    _SNAPSHOT_CACHE[cache_key] = (now, snapshot)
    return snapshot


# --- system utilities --------------------------------------------------------

def get_system_stats() -> Dict[str, float]:
    """Get current system performance statistics."""
    process = psutil.Process(os.getpid())

    return {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_mb": process.memory_info().rss / 1024 / 1024,
        "memory_percent": process.memory_percent(),
        "disk_io_read_mb": psutil.disk_io_counters().read_bytes / 1024 / 1024
        if psutil.disk_io_counters()
        else 0,
        "disk_io_write_mb": psutil.disk_io_counters().write_bytes / 1024 / 1024
        if psutil.disk_io_counters()
        else 0,
        "open_files": len(process.open_files()),
        "threads": process.num_threads(),
    }


def performance_report() -> str:
    """Generate a comprehensive performance report."""
    route_stats = monitor.get_route_stats()
    recent_metrics = monitor.get_recent_metrics(20)
    cache_hit_rate = monitor.get_cache_hit_rate()
    system_stats = get_system_stats()

    report = []
    report.append("=== PERFORMANCE REPORT ===\n")
    report.append(f"Cache Hit Rate: {cache_hit_rate:.1f}%")
    report.append(f"Cache Requests: {monitor.cache_stats['total_requests']}")
    report.append("")
    report.append("Route Performance:")
    for route, stats in sorted(
        route_stats.items(), key=lambda x: x[1]["avg_time"], reverse=True
    ):
        report.append(f"  {route}:")
        report.append(f"    Avg: {stats['avg_time']*1000:.1f}ms")
        report.append(f"    Min: {stats['min_time']*1000:.1f}ms")
        report.append(f"    Max: {stats['max_time']*1000:.1f}ms")
        report.append(f"    Requests: {stats['request_count']}")
    report.append("")
    report.append("System Performance:")
    report.append(f"  CPU: {system_stats['cpu_percent']:.1f}%")
    report.append(
        f"  Memory: {system_stats['memory_mb']:.1f}MB ({system_stats['memory_percent']:.1f}%)"
    )
    report.append(f"  Open Files: {system_stats['open_files']}")
    report.append(f"  Threads: {system_stats['threads']}")
    report.append("")
    slow_ops = [m for m in recent_metrics if m.duration > 0.1]
    if slow_ops:
        report.append("Recent Slow Operations (>100ms):")
        for op in sorted(slow_ops, key=lambda x: x.duration, reverse=True)[:10]:
            report.append(f"  {op.name}: {op.duration*1000:.1f}ms")
        report.append("")

    return "\n".join(report)


def load_test_simulation(base_url: str = "http://localhost:5000", num_requests: int = 100):
    """Simple load testing simulation."""
    import concurrent.futures
    import random
    import requests

    def make_request(url: str) -> Dict[str, Any]:
        start = time.time()
        try:
            response = requests.get(url, timeout=10)
            end = time.time()
            return {
                "url": url,
                "status": response.status_code,
                "duration": end - start,
                "success": response.status_code == 200,
            }
        except Exception as exc:
            end = time.time()
            return {
                "url": url,
                "status": 0,
                "duration": end - start,
                "success": False,
                "error": str(exc),
            }

    endpoints = [
        "/",
        "/favorites",
        "/tags",
        "/random",
    ]

    results: List[Dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for _ in range(num_requests):
            endpoint = random.choice(endpoints[:-1])
            url = base_url + endpoint
            futures.append(executor.submit(make_request, url))

        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    if successful:
        avg_time = sum(r["duration"] for r in successful) / len(successful)
        min_time = min(r["duration"] for r in successful)
        max_time = max(r["duration"] for r in successful)

        print("\nLoad Test Results:")
        print(f"  Total Requests: {len(results)}")
        print(f"  Successful: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
        print(f"  Failed: {len(failed)}")
        print(f"  Average Response Time: {avg_time*1000:.1f}ms")
        print(f"  Min Response Time: {min_time*1000:.1f}ms")
        print(f"  Max Response Time: {max_time*1000:.1f}ms")

        if failed:
            print("\nFailures:")
            for failure in failed[:5]:
                print(f"  {failure['url']}: {failure.get('error', 'Unknown error')}")

    return results


if __name__ == "__main__":
    print("Performance monitoring utilities loaded")
    print("Use performance_monitor decorator, flask_route_monitor, or load_test_simulation")
