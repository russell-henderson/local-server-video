"""
backend/app/core/rate_limiter.py

IP-based rate limiting for API endpoints.
Uses in-memory counters with TTL to track requests per IP address.
"""

import time
from typing import Dict, Tuple
from threading import RLock
from collections import defaultdict


class RateLimiter:
    """
    Rate limiter using sliding window approach.

    Tracks requests per IP address with time-based expiration.
    Stores: {ip: [(timestamp, None), ...]}
    Window slides automatically as old entries expire.
    """

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """
        Initialize rate limiter.

        Args:
            max_requests: Max requests allowed in time window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = RLock()

    def is_allowed(self, ip_address: str) -> Tuple[bool, Dict[str, int]]:
        """
        Check if request from IP is allowed.

        Args:
            ip_address: Client IP address

        Returns:
            Tuple of (allowed: bool, info: {remaining, reset_in})
        """
        with self.lock:
            now = time.time()
            window_start = now - self.window_seconds

            # Clean old entries outside window
            if ip_address in self.requests:
                self.requests[ip_address] = [
                    ts for ts in self.requests[ip_address]
                    if ts > window_start
                ]

            current_count = len(self.requests[ip_address])
            remaining = max(0, self.max_requests - current_count - 1)

            # Calculate reset time (oldest request in window)
            if self.requests[ip_address]:
                oldest = min(self.requests[ip_address])
                reset_in = max(1, int(oldest + self.window_seconds - now))
            else:
                reset_in = 0

            if current_count < self.max_requests:
                # Allow request and record timestamp
                self.requests[ip_address].append(now)
                return True, {
                    "remaining": remaining,
                    "reset_in": reset_in
                }
            else:
                # Rate limit exceeded
                return False, {
                    "remaining": 0,
                    "reset_in": reset_in
                }

    def reset(self, ip_address: str) -> None:
        """Clear request history for IP address."""
        with self.lock:
            if ip_address in self.requests:
                self.requests[ip_address].clear()

    def reset_all(self) -> None:
        """Clear all request history."""
        with self.lock:
            self.requests.clear()

    def get_stats(self, ip_address: str) -> Dict[str, int]:
        """
        Get current stats for IP address.

        Args:
            ip_address: Client IP address

        Returns:
            Dict with count, max, remaining
        """
        with self.lock:
            now = time.time()
            window_start = now - self.window_seconds

            # Clean old entries
            if ip_address in self.requests:
                self.requests[ip_address] = [
                    ts for ts in self.requests[ip_address]
                    if ts > window_start
                ]

            current_count = len(self.requests[ip_address])
            return {
                "count": current_count,
                "max": self.max_requests,
                "remaining": max(0, self.max_requests - current_count)
            }


# Global rate limiter instance
_rate_limiter = None


def get_rate_limiter(max_requests: int = 10,
                     window_seconds: int = 60) -> RateLimiter:
    """
    Get global rate limiter instance (singleton).

    Args:
        max_requests: Max requests per window (default 10)
        window_seconds: Window size in seconds (default 60)

    Returns:
        RateLimiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(max_requests, window_seconds)
    return _rate_limiter
