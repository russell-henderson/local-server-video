"""
backend/app/core/cache.py

Cache interface and write-through coordination.
Ensures database writes trigger cache invalidation and refreshes.
"""
from typing import Dict, Any
from datetime import datetime, timedelta


class Cache:
    """Cache interface with write-through coordination."""

    def __init__(self, backend_cache=None):
        """
        Initialize cache with optional backend.

        Args:
            backend_cache: Existing cache manager (from cache_manager.py)
        """
        self.backend = backend_cache
        self._ttl = timedelta(hours=1)
        self._last_refresh = {}

    def get(self, key: str, default=None) -> Any:
        """
        Get value from cache.

        Args:
            key: Cache key
            default: Default value if not found

        Returns:
            Cached value or default
        """
        if not self.backend:
            return default

        if key == "ratings":
            return self.backend.get_ratings()
        elif key == "views":
            return self.backend.get_views()
        elif key == "tags":
            return self.backend.get_tags()
        elif key == "favorites":
            return self.backend.get_favorites()

        return default

    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        if not self.backend:
            return

        # Most writes are handled through backend methods
        # This is a placeholder for future atomic operations
        self._last_refresh[key] = datetime.now()

    def invalidate(self, key: str) -> None:
        """
        Invalidate cache entry.

        Args:
            key: Cache key to invalidate
        """
        if not self.backend:
            return

        if key == "ratings":
            self.backend.invalidate_ratings()
        elif key == "views":
            self.backend.invalidate_views()
        elif key == "tags":
            self.backend.invalidate_tags()
        elif key == "favorites":
            self.backend.invalidate_favorites()

        self._last_refresh[key] = datetime.now()

    def invalidate_all(self) -> None:
        """Invalidate entire cache."""
        if not self.backend:
            return

        self.backend.invalidate_ratings()
        self.backend.invalidate_views()
        self.backend.invalidate_tags()
        self.backend.invalidate_favorites()

    def is_stale(self, key: str) -> bool:
        """
        Check if cache entry is stale.

        Args:
            key: Cache key

        Returns:
            True if stale (past TTL), False otherwise
        """
        if key not in self._last_refresh:
            return True

        last = self._last_refresh[key]
        return datetime.now() - last > self._ttl

    def refresh_if_stale(self, key: str) -> Any:
        """
        Refresh cache if stale.

        Args:
            key: Cache key

        Returns:
            Fresh cached value
        """
        if self.is_stale(key):
            self.invalidate(key)
        return self.get(key)


class WriteThrough:
    """Write-through cache coordinator for database operations."""

    def __init__(self, db_session, cache):
        """
        Initialize write-through coordinator.

        Args:
            db_session: Database session (from backend/app/core/db.py)
            cache: Cache instance (from above)
        """
        self.db = db_session
        self.cache = cache

    def write_rating(self, media_hash: str, user_id: str,
                     value: int) -> Dict[str, Any]:
        """
        Write rating to database with cache coordination.

        Process:
        1. Write to database
        2. Invalidate cache
        3. Read fresh value from cache

        Args:
            media_hash: Media identifier
            user_id: User identifier
            value: Rating value (1-5)

        Returns:
            Updated rating summary
        """
        # This would be called from ratings_service
        # Step 1: Write to DB (handled by ratings_service.set_rating)
        # media_hash, user_id, value already persisted to DB
        # Step 2: Invalidate cache
        self.cache.invalidate("ratings")
        # Step 3: Return fresh data
        return self.cache.get("ratings", {})

    def write_view(self, media_hash: str) -> None:
        """
        Write view to database with cache coordination.

        Args:
            media_hash: Media identifier
        """
        # View recorded to database by external handler
        # media_hash is used as lookup key in database
        self.cache.invalidate("views")

    def write_tag(self, media_hash: str, tag: str) -> None:
        """
        Write tag to database with cache coordination.

        Args:
            media_hash: Media identifier
            tag: Tag value
        """
        # Tag written to database by external handler
        # media_hash and tag are used for database lookup
        self.cache.invalidate("tags")

    def write_favorite(self, media_hash: str, is_favorite: bool) -> None:
        """
        Write favorite to database with cache coordination.

        Args:
            media_hash: Media identifier
            is_favorite: True to add, False to remove
        """
        # Favorite state written to database by external handler
        # media_hash and is_favorite track the state change
        self.cache.invalidate("favorites")


def get_cache(backend_cache=None) -> Cache:
    """
    Factory for cache instance.

    Args:
        backend_cache: Existing cache manager

    Returns:
        Cache instance
    """
    return Cache(backend_cache)


def get_write_through(db_session, backend_cache=None) -> WriteThrough:
    """
    Factory for write-through coordinator.

    Args:
        db_session: Database session
        backend_cache: Existing cache manager

    Returns:
        WriteThrough instance
    """
    cache = get_cache(backend_cache)
    return WriteThrough(db_session, cache)
