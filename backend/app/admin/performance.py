"""Performance metrics tracking."""
import time
import threading
from collections import defaultdict
from statistics import quantiles


class PerformanceMetrics:
    """Track cache hits, endpoint latency, DB queries."""

    def __init__(self):
        self.lock = threading.RLock()
        self.cache_hits = 0
        self.cache_misses = 0
        self.endpoint_latencies = defaultdict(list)
        self.db_queries_per_request = []
        self.total_db_queries = 0
        self.start_time = time.time()

    def record_cache_hit(self):
        """Record a cache hit."""
        with self.lock:
            self.cache_hits += 1

    def record_cache_miss(self):
        """Record a cache miss."""
        with self.lock:
            self.cache_misses += 1

    def get_cache_hit_rate(self) -> float:
        """Return cache hit rate as percentage (0-100)."""
        with self.lock:
            total = self.cache_hits + self.cache_misses
            return (self.cache_hits / total * 100) if total else 0.0

    def get_uptime_seconds(self) -> float:
        """Return uptime in seconds."""
        return time.time() - self.start_time


_metrics = None


def get_metrics():
    """Get global metrics singleton."""
    global _metrics
    if _metrics is None:
        _metrics = PerformanceMetrics()
    return _metrics
