"""Performance metrics tracking."""
import time
import threading
from collections import defaultdict
from statistics import quantiles, mean


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
        # Specifically track POST /api/ratings latencies
        self.ratings_post_latencies = []

    def record_cache_hit(self):
        """Record a cache hit."""
        with self.lock:
            self.cache_hits += 1

    def record_cache_miss(self):
        """Record a cache miss."""
        with self.lock:
            self.cache_misses += 1

    def record_endpoint_latency(self, endpoint: str, latency: float):
        """Record endpoint latency in seconds."""
        with self.lock:
            self.endpoint_latencies[endpoint].append(latency)
            if endpoint == 'POST /api/ratings':
                self.ratings_post_latencies.append(latency)

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
            if not self.ratings_post_latencies:
                return 0.0
            if len(self.ratings_post_latencies) == 1:
                return self.ratings_post_latencies[0] * 1000
            # Get 95th percentile
            p95_list = quantiles(
                self.ratings_post_latencies,
                n=20  # Creates 19 cut points; index 18 is 95th percentile
            )
            return p95_list[18] * 1000  # Convert to ms

    def get_ratings_post_avg_latency(self) -> float:
        """Return average latency for POST /api/ratings in ms."""
        with self.lock:
            if not self.ratings_post_latencies:
                return 0.0
            return mean(self.ratings_post_latencies) * 1000  # Convert to ms

    def get_ratings_post_count(self) -> int:
        """Return number of POST /api/ratings requests."""
        with self.lock:
            return len(self.ratings_post_latencies)


_metrics = None


def get_metrics():
    """Get global metrics singleton."""
    global _metrics
    if _metrics is None:
        _metrics = PerformanceMetrics()
    return _metrics
