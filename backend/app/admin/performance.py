"""Performance metrics tracking."""
from __future__ import annotations

import time
import threading
from collections import defaultdict, deque
from statistics import quantiles, mean
from typing import Deque, Dict, List, Optional, Tuple

# Default windows (seconds)
DEFAULT_WINDOW_SECONDS = 900
MAX_WINDOW_SECONDS = 3600
MAX_SAMPLES_PER_ROUTE = 500


class PerformanceMetrics:
    """
    Track cache hits, endpoint latency, DB queries, and uptime.

    Samples are stored in rolling deques capped both by time (MAX_WINDOW_SECONDS)
    and by length (MAX_SAMPLES_PER_ROUTE) to keep memory bounded.
    """

    def __init__(self):
        self.lock = threading.RLock()
        self.cache_hits = 0
        self.cache_misses = 0

        # Samples: {route_key -> deque[dict]}
        self.route_samples: Dict[str, Deque[Dict]] = defaultdict(deque)
        self.global_samples: Deque[Dict] = deque()

        # DB query fanout per request (rolling window)
        self.db_queries_per_request: Deque[int] = deque()
        self.start_time = time.time()

        # Ratings POST samples in milliseconds (rolling window)
        self.ratings_post_latencies: Deque[float] = deque()

    # --- recorders -----------------------------------------------------

    def _prune_deque(self, dq: Deque[Dict]) -> None:
        """Remove samples older than MAX_WINDOW_SECONDS and cap length."""
        cutoff = time.time() - MAX_WINDOW_SECONDS
        while dq and dq[0]["timestamp"] < cutoff:
            dq.popleft()
        while len(dq) > MAX_SAMPLES_PER_ROUTE:
            dq.popleft()

    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        with self.lock:
            self.cache_hits += 1

    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        with self.lock:
            self.cache_misses += 1

    def record_db_queries(self, count: int) -> None:
        """Record number of DB queries for a request."""
        with self.lock:
            self.db_queries_per_request.append(count)
            if len(self.db_queries_per_request) > MAX_SAMPLES_PER_ROUTE:
                self.db_queries_per_request.popleft()

    def record_endpoint_latency(
        self,
        endpoint: str,
        latency_seconds: float,
        *,
        status_code: int = 200,
        method: Optional[str] = None,
        path: Optional[str] = None,
        endpoint_name: Optional[str] = None,
        remote_addr: Optional[str] = None,
    ) -> None:
        """
        Record endpoint latency in seconds.

        `endpoint` is kept for backward compatibility (e.g., "POST /api/ratings").
        Additional metadata (method/path/endpoint_name) help build richer summaries.
        """
        timestamp = time.time()
        duration_ms = max(latency_seconds * 1000.0, 0.0)
        route_key = endpoint
        if method and path:
            route_key = f"{method} {path}"

        sample = {
            "route_key": route_key,
            "method": method or (endpoint.split(" ")[0] if " " in endpoint else None),
            "path": path or (endpoint.split(" ", 1)[1] if " " in endpoint else None),
            "endpoint": endpoint_name or endpoint,
            "duration_ms": duration_ms,
            "status_code": status_code,
            "timestamp": timestamp,
            "remote_addr": remote_addr,
        }

        with self.lock:
            dq = self.route_samples[route_key]
            dq.append(sample)
            self._prune_deque(dq)

            self.global_samples.append(sample)
            self._prune_deque(self.global_samples)

            if route_key.startswith("POST") and "/api/ratings" in route_key:
                self.ratings_post_latencies.append(duration_ms)
                if len(self.ratings_post_latencies) > MAX_SAMPLES_PER_ROUTE:
                    self.ratings_post_latencies.popleft()

    # --- computed helpers ----------------------------------------------

    def _get_latency_percentiles(self, values: List[float]) -> Tuple[float, float, float]:
        """Return p50, p95, p99 from a list of latency values (ms)."""
        if not values:
            return 0.0, 0.0, 0.0
        if len(values) == 1:
            val = float(values[0])
            return val, val, val
        percentile_list = quantiles(values, n=100)
        return percentile_list[49], percentile_list[94], percentile_list[98]

    def get_cache_hit_rate(self) -> float:
        """Return cache hit rate as percentage (0-100)."""
        with self.lock:
            total = self.cache_hits + self.cache_misses
            return (self.cache_hits / total * 100) if total else 0.0

    def get_uptime_seconds(self) -> float:
        """Return uptime in seconds."""
        return time.time() - self.start_time

    def get_ratings_post_p95_latency(self) -> float:
        """Return P95 latency for POST /api/ratings in ms."""
        with self.lock:
            p50, p95, _p99 = self._get_latency_percentiles(list(self.ratings_post_latencies))
            return p95

    def get_ratings_post_avg_latency(self) -> float:
        """Return average latency for POST /api/ratings in ms."""
        with self.lock:
            if not self.ratings_post_latencies:
                return 0.0
            return mean(self.ratings_post_latencies)

    def get_ratings_post_count(self) -> int:
        """Return number of POST /api/ratings requests."""
        with self.lock:
            return len(self.ratings_post_latencies)


_metrics: Optional[PerformanceMetrics] = None


def get_metrics() -> PerformanceMetrics:
    """Get global metrics singleton."""
    global _metrics
    if _metrics is None:
        _metrics = PerformanceMetrics()
    return _metrics
