"""
backend/services/ratings_service.py

Ratings business logic service.
Handles getting and setting ratings with database and cache coordination.
Uses media_hash identifiers with bidirectional filename lookup.
"""
from typing import Dict, Optional, Tuple, Any
import hashlib
import logging
import time
from pathlib import Path


class RatingsService:
    """Service for managing video ratings."""
    
    def __init__(self, cache, database):
        """
        Initialize ratings service.
        
        Args:
            cache: Cache manager instance
            database: Database instance
        """
        self.cache = cache
        self.database = database
        self._logger = logging.getLogger(__name__)
        # Lazy hash index to avoid repeated full scans on hash misses.
        self._hash_index: Dict[str, str] = {}
        self._hash_index_last_refresh = 0.0
        self._hash_index_ttl_seconds = 300.0
    
    @staticmethod
    def get_media_hash(filename: str) -> str:
        """
        Generate SHA256-based media hash for a filename.
        
        Args:
            filename: Video filename
            
        Returns:
            SHA256 hash of the filename (16-char hex prefix)
        """
        return hashlib.sha256(filename.encode()).hexdigest()[:16]
    
    def get_filename_by_hash(self, media_hash: str) -> Optional[str]:
        """
        Resolve media_hash to filename via persistent lookup.
        
        Args:
            media_hash: Media hash identifier
            
        Returns:
            Filename if found, else None
        """
        if not self.database:
            return None

        # Primary lookup through persisted mapping table.
        filename = self.database.get_filename_by_hash(media_hash)
        if filename:
            return filename

        # Fallback: consult a lazily refreshed in-memory hash index so misses
        # do not trigger a full database filename scan every time.
        candidate = self._lookup_filename_from_hash_index(media_hash)
        if candidate:
            self.database.register_media_hash(media_hash, candidate)
            return candidate

        return None

    def _lookup_filename_from_hash_index(self, media_hash: str) -> Optional[str]:
        """
        Resolve media hash from an in-memory filename hash index.
        Rebuilds index only when stale to avoid repeated full-table scans.
        """
        now = time.time()
        if (
            not self._hash_index
            or (now - self._hash_index_last_refresh) > self._hash_index_ttl_seconds
        ):
            self._refresh_hash_index()
        return self._hash_index.get(media_hash)

    def _refresh_hash_index(self) -> None:
        """Rebuild hash index from known filenames."""
        if not self.database:
            self._hash_index = {}
            self._hash_index_last_refresh = time.time()
            return

        if not hasattr(self.database, "get_all_filenames"):
            self._logger.error(
                "Ratings database is missing required method get_all_filenames"
            )
            raise AttributeError("Database missing get_all_filenames")

        all_filenames = self.database.get_all_filenames()
        self._hash_index = {
            self.get_media_hash(filename): filename
            for filename in all_filenames
        }
        self._hash_index_last_refresh = time.time()
    
    def register_media_hash(self, filename: str) -> str:
        """
        Register filename and generate/store media_hash.
        
        Args:
            filename: Video filename
            
        Returns:
            Generated media hash
        """
        media_hash = self.get_media_hash(filename)
        if self.database:
            self.database.register_media_hash(media_hash, filename)
        return media_hash
    
    def get_rating(self, media_hash: str) -> Optional[int]:
        """
        Get a single rating value.
        
        Args:
            media_hash: Media hash identifier
            
        Returns:
            Rating value 1-5, or None if not rated
        """
        filename = self.get_filename_by_hash(media_hash)
        if not filename:
            return None
        
        # Try cache first
        ratings = self.cache.get_ratings()
        return ratings.get(filename)
    
    def get_rating_summary(self, media_hash: str) -> Dict[str, Any]:
        """
        Get rating summary (average, count, user rating).
        
        Args:
            media_hash: Media hash identifier
            
        Returns:
            Dict with keys: average, count, user (with value field)
        """
        filename = self.get_filename_by_hash(media_hash)
        if not filename:
            return {
                "average": 0.0,
                "count": 0,
                "user": None
            }
        
        # Get all ratings from cache
        ratings = self.cache.get_ratings()
        user_rating = ratings.get(filename)
        
        # For single-user system, treat user rating as the only rating
        if user_rating:
            return {
                "average": float(user_rating),
                "count": 1,
                "user": {"value": user_rating}
            }
        
        return {
            "average": 0.0,
            "count": 0,
            "user": None
        }
    
    def set_rating(self, media_hash: str, value: int) -> Dict[str, Any]:
        """
        Set a rating value (maps API value -> DB rating column).
        
        Args:
            media_hash: Media hash identifier
            value: Rating value 1-5 (from API payload 'value' field)
            
        Returns:
            Updated rating summary
            
        Raises:
            ValueError: If value not in 1-5 range
            FileNotFoundError: If video file not found
        """
        if value < 1 or value > 5:
            raise ValueError(f"Rating must be 1-5, got {value}")
        
        filename = self.get_filename_by_hash(media_hash)
        if not filename:
            raise FileNotFoundError(f"No video found for hash: {media_hash}")
        
        # Check if file exists
        video_path = Path("videos") / filename
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {filename}")
        
        # Write to database (maps API 'value' -> DB 'rating' column)
        if self.database and self.database.get_connection():
            try:
                with self.database.get_connection() as conn:
                    # INSERT OR REPLACE uses 'rating' column (not 'value')
                    conn.execute("""
                        INSERT OR REPLACE INTO ratings (filename, rating)
                        VALUES (?, ?)
                    """, (filename, value))
                    conn.commit()
            except Exception as e:
                # Fall back to cache if database fails
                print(f"Database write failed: {e}, using cache fallback")
        
        # Update cache by invalidating it
        self.cache.invalidate_ratings()
        
        # Get fresh summary
        return self.get_rating_summary(media_hash)
    
    def validate_rating(self, value: any) -> Tuple[bool, Optional[str]]:
        """
        Validate rating value.
        
        Args:
            value: Value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(value, int):
            return False, "Rating must be an integer"
        
        if value < 1 or value > 5:
            return False, "Rating must be between 1 and 5"
        
        return True, None
