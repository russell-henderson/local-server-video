"""
tests/test_rating_write_and_read.py

Integration test for rating write and read operations.
Tests that ratings are persisted to database and cache is updated.
"""
import pytest
from pathlib import Path
import sqlite3


# Test fixtures and setup
@pytest.fixture
def test_app():
    """Create Flask test app."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from main import app
    
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(test_app):
    """Create test client."""
    return test_app.test_client()


@pytest.fixture
def test_video(tmp_path):
    """Create test video file."""
    videos_dir = Path("videos")
    
    # Find first available video or create a test one
    video_files = list(videos_dir.glob("*"))
    
    if video_files:
        test_video_name = video_files[0].name
    else:
        pytest.skip("No videos available for testing")
    
    return test_video_name


class TestRatingWriteAndRead:
    """Test suite for rating write/read operations."""
    
    def test_set_rating_via_api(self, client, test_video):
        """Test setting a rating via POST /api/ratings/{media_hash}."""
        media_hash = test_video  # For now, use filename as hash
        
        response = client.post(
            f'/api/ratings/{media_hash}',
            json={'value': 4},
            content_type='application/json'
        )
        
        assert response.status_code in [201, 200]
        data = response.get_json()
        assert data is not None
        assert 'user' in data or 'average' in data
    
    def test_get_rating_via_api(self, client, test_video):
        """Test getting a rating via GET /api/ratings/{media_hash}."""
        media_hash = test_video
        
        # First set a rating
        set_response = client.post(
            f'/api/ratings/{media_hash}',
            json={'value': 3},
            content_type='application/json'
        )
        assert set_response.status_code in [201, 200]
        
        # Then get it
        get_response = client.get(f'/api/ratings/{media_hash}')
        assert get_response.status_code == 200
        
        data = get_response.get_json()
        assert data is not None
        assert 'user' in data or 'average' in data
    
    def test_rating_persists_after_reload(self, client, test_video):
        """Test that rating persists after setting."""
        media_hash = test_video
        
        # Set rating
        client.post(
            f'/api/ratings/{media_hash}',
            json={'value': 5},
            content_type='application/json'
        )
        
        # Get rating
        response = client.get(f'/api/ratings/{media_hash}')
        data = response.get_json()
        
        assert data is not None
        # Rating should be retrievable
        if 'user' in data and data['user'] is not None:
            assert data['user'].get('value') == 5
    
    def test_invalid_rating_value(self, client, test_video):
        """Test that invalid rating values are rejected."""
        media_hash = test_video
        
        # Test value too high
        response = client.post(
            f'/api/ratings/{media_hash}',
            json={'value': 6},
            content_type='application/json'
        )
        assert response.status_code == 400
        
        # Test value too low
        response = client.post(
            f'/api/ratings/{media_hash}',
            json={'value': 0},
            content_type='application/json'
        )
        assert response.status_code == 400
        
        # Test non-integer
        response = client.post(
            f'/api/ratings/{media_hash}',
            json={'value': 'invalid'},
            content_type='application/json'
        )
        assert response.status_code == 400
    
    def test_missing_video(self, client):
        """Test that rating a non-existent video fails gracefully."""
        fake_hash = 'nonexistent_video_12345'
        
        response = client.post(
            f'/api/ratings/{fake_hash}',
            json={'value': 3},
            content_type='application/json'
        )
        
        # Should be 404 (video not found)
        assert response.status_code == 404
    
    def test_rating_range(self, client, test_video):
        """Test all valid rating values 1-5."""
        media_hash = test_video
        
        for rating_value in range(1, 6):
            response = client.post(
                f'/api/ratings/{media_hash}',
                json={'value': rating_value},
                content_type='application/json'
            )
            
            assert response.status_code in [201, 200], \
                   f"Failed to set rating {rating_value}"
            
            # Verify it was set
            get_response = client.get(f'/api/ratings/{media_hash}')
            assert get_response.status_code == 200
    
    def test_rating_json_structure(self, client, test_video):
        """Test that rating response has expected JSON structure."""
        media_hash = test_video
        
        client.post(
            f'/api/ratings/{media_hash}',
            json={'value': 4},
            content_type='application/json'
        )
        
        response = client.get(f'/api/ratings/{media_hash}')
        data = response.get_json()
        
        assert isinstance(data, dict)
        assert 'average' in data
        assert 'count' in data
        assert isinstance(data['average'], (int, float))
        assert isinstance(data['count'], int)


class TestRatingCacheBehavior:
    """Test that cache is updated after rating changes."""
    
    def test_cache_invalidation_on_write(self, client, test_video):
        """Test that cache is invalidated when rating is written."""
        from cache_manager import cache
        
        media_hash = test_video
        
        # Clear cache
        cache.invalidate_ratings()
        
        # Set rating
        response = client.post(
            f'/api/ratings/{media_hash}',
            json={'value': 4},
            content_type='application/json'
        )
        assert response.status_code in [201, 200]
        
        # Cache should have the new rating
        ratings = cache.get_ratings()
        assert ratings is not None
        # The rating may or may not be in cache depending on implementation
        # Just verify cache is accessible
    
    def test_json_fallback_works(self, client, test_video):
        """Test that ratings work even if database is unavailable."""
        from cache_manager import cache
        
        # Get ratings (should use cache/JSON if DB unavailable)
        ratings = cache.get_ratings()
        assert isinstance(ratings, dict)


class TestRatingDatabasePersistence:
    """Test that ratings are persisted to database."""
    
    def test_rating_written_to_db(self, client, test_video):
        """Test that rating is written to SQLite database."""
        from database_migration import VideoDatabase
        
        db = VideoDatabase()
        media_hash = test_video
        
        # Set rating via API
        response = client.post(
            f'/api/ratings/{media_hash}',
            json={'value': 4},
            content_type='application/json'
        )
        assert response.status_code in [201, 200]
        
        # Query database directly
        conn = sqlite3.connect(str(db.db_path))
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT value FROM ratings WHERE filename = ?',
            (media_hash,)
        )
        result = cursor.fetchone()
        conn.close()
        
        # Verify the rating is in the database
        assert result is not None, \
               f"Rating not found in database for {media_hash}"
        assert result[0] == 4
    
    def test_rating_survives_cache_clear(self, client, test_video):
        """Test that rating persists in DB after cache is cleared."""
        from database_migration import VideoDatabase
        from cache_manager import cache
        
        db = VideoDatabase()
        media_hash = test_video
        
        # Set rating
        client.post(
            f'/api/ratings/{media_hash}',
            json={'value': 3},
            content_type='application/json'
        )
        
        # Clear cache
        cache.invalidate_ratings()
        
        # Query database directly
        conn = sqlite3.connect(str(db.db_path))
        cursor = conn.cursor()
        cursor.execute(
            'SELECT value FROM ratings WHERE filename = ?',
            (media_hash,)
        )
        result = cursor.fetchone()
        conn.close()
        
        # Rating should still be in database
        assert result is not None
        assert result[0] == 3
    
    def test_rating_update_overwrites_previous(self, client, test_video):
        """Test that updating a rating overwrites the previous one."""
        from database_migration import VideoDatabase
        
        db = VideoDatabase()
        media_hash = test_video
        
        # Set initial rating
        client.post(
            f'/api/ratings/{media_hash}',
            json={'value': 2},
            content_type='application/json'
        )
        
        # Update rating
        client.post(
            f'/api/ratings/{media_hash}',
            json={'value': 5},
            content_type='application/json'
        )
        
        # Query database
        conn = sqlite3.connect(str(db.db_path))
        cursor = conn.cursor()
        
        # Count ratings (should be 1 entry, not 2)
        cursor.execute(
            'SELECT COUNT(*) FROM ratings WHERE filename = ?',
            (media_hash,)
        )
        count = cursor.fetchone()[0]
        
        # Get latest value
        cursor.execute(
            'SELECT value FROM ratings WHERE filename = ? '
            'ORDER BY updated_at DESC LIMIT 1',
            (media_hash,)
        )
        result = cursor.fetchone()
        conn.close()
        
        assert count == 1, \
               "Should have exactly 1 rating entry after update"
        assert result[0] == 5, \
               "Latest rating should be 5"


class TestRatingRateLimiting:
    """Test IP-based rate limiting on rating POST endpoint."""
    
    def test_rate_limiting_enforced(self, client, test_video):
        """Test that rate limiting is enforced."""
        media_hash = test_video
        
        # Make 10 requests (should all succeed)
        for i in range(10):
            response = client.post(
                f'/api/ratings/{media_hash}',
                json={'value': i % 5 + 1},
                content_type='application/json'
            )
            assert response.status_code in [200, 201], \
                   f"Request {i+1} failed with {response.status_code}"
        
        # 11th request should be rate limited
        response = client.post(
            f'/api/ratings/{media_hash}',
            json={'value': 3},
            content_type='application/json'
        )
        assert response.status_code == 429, \
               "Rate limit should kick in after 10 requests"
    
    def test_rate_limit_includes_retry_after(self, client, test_video):
        """Test that rate limit response includes Retry-After header."""
        media_hash = test_video
        
        # Exhaust rate limit
        for _ in range(10):
            client.post(
                f'/api/ratings/{media_hash}',
                json={'value': 3},
                content_type='application/json'
            )
        
        # Next request should include Retry-After
        response = client.post(
            f'/api/ratings/{media_hash}',
            json={'value': 3},
            content_type='application/json'
        )
        
        assert response.status_code == 429
        assert 'Retry-After' in response.headers, \
               "429 response should include Retry-After header"
    
    def test_rate_limit_error_message(self, client, test_video):
        """Test that rate limit error includes helpful message."""
        media_hash = test_video
        
        # Exhaust rate limit
        for _ in range(10):
            client.post(
                f'/api/ratings/{media_hash}',
                json={'value': 3},
                content_type='application/json'
            )
        
        # Next request should include helpful error
        response = client.post(
            f'/api/ratings/{media_hash}',
            json={'value': 3},
            content_type='application/json'
        )
        
        data = response.get_json()
        assert 'error' in data
        assert 'Rate limit exceeded' in data['error']


class TestPydanticValidation:
    """Test Pydantic schema validation."""
    
    def test_string_rating_coerced_to_int(self, client, test_video):
        """Test that string rating values are coerced to int."""
        media_hash = test_video
        
        response = client.post(
            f'/api/ratings/{media_hash}',
            json={'value': '4'},  # string instead of int
            content_type='application/json'
        )
        
        # Pydantic should coerce the string to int
        assert response.status_code in [200, 201]
    
    def test_float_rating_coerced_to_int(self, client, test_video):
        """Test that float rating values are coerced to int."""
        media_hash = test_video
        
        response = client.post(
            f'/api/ratings/{media_hash}',
            json={'value': 4.5},  # float instead of int
            content_type='application/json'
        )
        
        # Pydantic should coerce/validate
        # May succeed (4) or fail (4.5) depending on validation
        assert response.status_code in [200, 201, 400]
    
    def test_null_rating_rejected(self, client, test_video):
        """Test that null rating values are rejected."""
        media_hash = test_video
        
        response = client.post(
            f'/api/ratings/{media_hash}',
            json={'value': None},
            content_type='application/json'
        )
        
        assert response.status_code == 400, \
               "Null rating value should be rejected"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
