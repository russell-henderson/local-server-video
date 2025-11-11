"""
backend/services/ratings_service.py

Ratings business logic service.
Handles getting and setting ratings with database and cache coordination.
Supports both filename and media_hash identifiers.
"""
from typing import Dict, Optional, Tuple
import hashlib
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
    
    @staticmethod
    def get_media_hash(filename: str) -> str:
        """
        Generate or retrieve media_hash for a filename.
        Currently generates SHA256 hash of the filename.
        
        In a full implementation, this would be based on file content
        or a persistent mapping stored in the database.
        
        Args:
            filename: Video filename
            
        Returns:
            SHA256 hash of the filename (hex)
        """
        return hashlib.sha256(filename.encode()).hexdigest()[:16]
    
    def get_rating(self, media_hash: str,
                   filename: Optional[str] = None) -> Optional[int]:
        """
        Get a single rating value.
        
        Args:
            media_hash: Media hash identifier (preferred)
            filename: Fallback filename if media_hash not found
            
        Returns:
            Rating value 1-5, or None if not rated
        """
        if not filename:
            # In a full implementation, media_hash would map to filename
            # For now, assume filename is encoded in media_hash
            filename = self._resolve_filename(media_hash)
        
        # Try cache first
        ratings = self.cache.get_ratings()
        return ratings.get(filename)
    
    def get_rating_summary(self, media_hash: str,
                           filename: Optional[str] = None) \
            -> Dict[str, any]:
        """
        Get rating summary (average, count, user rating).
        
        Args:
            media_hash: Media hash identifier
            filename: Fallback filename
            
        Returns:
            Dict with keys: average, count, user (value)
        """
        if not filename:
            filename = self._resolve_filename(media_hash)
        
        # Get all ratings from cache
        ratings = self.cache.get_ratings()
        user_rating = ratings.get(filename)
        
        # For now, treat the single rating as the only one
        # In a multi-user system, this would aggregate across users
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
    
    def set_rating(self, media_hash: str, value: int,
                   filename: Optional[str] = None) -> Dict[str, any]:
        """
        Set a rating value.
        
        Args:
            media_hash: Media hash identifier
            value: Rating value 1-5
            filename: Fallback filename
            
        Returns:
            Updated rating summary
            
        Raises:
            ValueError: If value not in 1-5 range
        """
        if value < 1 or value > 5:
            raise ValueError(f"Rating must be 1-5, got {value}")
        
        if not filename:
            filename = self._resolve_filename(media_hash)
        
        # Check if file exists
        video_path = Path("videos") / filename
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {filename}")
        
        # Write to database
        if self.database and self.database.get_connection():
            try:
                with self.database.get_connection() as conn:
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
        return self.get_rating_summary(media_hash, filename)
    
    def _resolve_filename(self, media_hash: str) -> str:
        """
        Resolve media_hash to filename.
        
        For now, assumes media_hash is derived from filename.
        In a full implementation, this would query a persistent mapping.
        
        Args:
            media_hash: Media hash (16-char SHA256 prefix)
            
        Returns:
            Filename, or media_hash itself as fallback
        """
        # TODO: Implement actual media_hash resolution
        # This would query a persistent mapping table
        # For now, return media_hash which should be filename
        return media_hash
    
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
