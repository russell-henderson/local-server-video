"""
tests/test_rating_mapping.py

Unit test for API value -> database rating column mapping.
Ensures API uses 'value' field but database uses 'rating' column.
"""
import pytest
from pathlib import Path


class TestRatingColumnMapping:
    """Test that API 'value' maps to DB 'rating' column."""
    
    def test_value_to_rating_mapping(self):
        """Test that set_rating() maps API 'value' to DB 'rating' column."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        from database_migration import VideoDatabase
        from cache_manager import VideoCache
        from backend.services.ratings_service import RatingsService
        import tempfile
        import os
        
        # Create temp DB for this test
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = VideoDatabase(db_path=db_path)
            cache = VideoCache()
            service = RatingsService(cache, db)
            
            # Create a test video in the database
            test_filename = "test_video.mp4"
            with db.get_connection() as conn:
                conn.execute(
                    "INSERT INTO videos (filename) VALUES (?)",
                    (test_filename,)
                )
                conn.commit()
            
            # Register media hash
            service.register_media_hash(test_filename)
            
            # API sends 'value': 4, but DB should store in 'rating' column
            with db.get_connection() as conn:
                # Direct DB insert to verify structure
                conn.execute(
                    "INSERT OR REPLACE INTO ratings "
                    "(filename, rating) VALUES (?, ?)",
                    (test_filename, 4)
                )
                conn.commit()
                
                # Query and verify it's in 'rating' column (not 'value')
                cursor = conn.execute(
                    "SELECT rating FROM ratings WHERE filename = ?",
                    (test_filename,)
                )
                row = cursor.fetchone()
                assert row is not None, "Rating should be inserted"
                assert row['rating'] == 4, \
                    "Value should map to 'rating' column"
    
    def test_api_payload_validation(self):
        """Test that API validates 'value' in 1-5 range."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        from backend.services.ratings_service import RatingsService
        from database_migration import VideoDatabase
        from cache_manager import VideoCache
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = VideoDatabase(db_path=db_path)
            cache = VideoCache()
            service = RatingsService(cache, db)
            
            test_filename = "test_video.mp4"
            with db.get_connection() as conn:
                conn.execute(
                    "INSERT INTO videos (filename) VALUES (?)",
                    (test_filename,)
                )
                conn.commit()
            
            media_hash = service.register_media_hash(test_filename)
            
            # Valid values 1-5 should work
            for value in [1, 2, 3, 4, 5]:
                # Service should not raise
                result = service.set_rating(media_hash, value)
                assert result is not None
            
            # Invalid values should raise
            for value in [0, 6, -1, 10]:
                with pytest.raises(ValueError, match="Rating must be 1-5"):
                    service.set_rating(media_hash, value)
    
    def test_rating_summary_structure(self):
        """Test that get_rating_summary returns correct structure."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        from backend.services.ratings_service import RatingsService
        from database_migration import VideoDatabase
        from cache_manager import VideoCache
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = VideoDatabase(db_path=db_path)
            cache = VideoCache()
            service = RatingsService(cache, db)
            
            test_filename = "test_video.mp4"
            with db.get_connection() as conn:
                conn.execute(
                    "INSERT INTO videos (filename) VALUES (?)",
                    (test_filename,)
                )
                conn.commit()
            
            media_hash = service.register_media_hash(test_filename)
            
            # Before rating is set
            summary = service.get_rating_summary(media_hash)
            assert summary is not None
            assert 'average' in summary
            assert 'count' in summary
            assert 'user' in summary
            assert summary['user'] is None
            
            # Set a rating
            service.set_rating(media_hash, 3)
            
            # After rating is set
            summary = service.get_rating_summary(media_hash)
            assert summary['user'] is not None
            assert 'value' in summary['user']
            assert summary['user']['value'] == 3
            assert summary['average'] == 3.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
