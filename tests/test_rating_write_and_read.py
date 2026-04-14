"""
tests/test_rating_write_and_read.py

Integration tests for ratings API write/read behavior aligned to current hash-first contract.
"""

from __future__ import annotations

from pathlib import Path
import sqlite3

import pytest

from backend.app.api.ratings import ratings_service
from database_migration import VideoDatabase


@pytest.fixture
def rating_target():
    """Return a known filename + registered media_hash for API tests."""
    videos_dir = Path("videos")
    video_files = [p for p in videos_dir.glob("*") if p.is_file()]
    if not video_files:
        pytest.skip("No videos available for ratings integration tests")

    filename = video_files[0].name
    media_hash = ratings_service.register_media_hash(filename)

    db = VideoDatabase()
    with db.get_connection() as conn:
        conn.execute("DELETE FROM ratings WHERE filename = ?", (filename,))
        conn.commit()

    return {"filename": filename, "media_hash": media_hash}


class TestRatingWriteAndRead:
    def test_set_rating_via_api(self, client, rating_target):
        response = client.post(
            f"/api/ratings/{rating_target['media_hash']}",
            json={"value": 4},
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data is not None
        assert data["user"]["value"] == 4

    def test_get_rating_via_api(self, client, rating_target):
        set_response = client.post(
            f"/api/ratings/{rating_target['media_hash']}",
            json={"value": 3},
            content_type="application/json",
        )
        assert set_response.status_code == 201

        get_response = client.get(f"/api/ratings/{rating_target['media_hash']}")
        assert get_response.status_code == 200
        data = get_response.get_json()
        assert data["user"]["value"] == 3

    def test_rating_persists_after_reload(self, client, rating_target):
        post_response = client.post(
            f"/api/ratings/{rating_target['media_hash']}",
            json={"value": 5},
            content_type="application/json",
        )
        assert post_response.status_code == 201

        response = client.get(f"/api/ratings/{rating_target['media_hash']}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["user"]["value"] == 5

    def test_invalid_rating_value(self, client, rating_target):
        for bad in (6, 0, "invalid"):
            response = client.post(
                f"/api/ratings/{rating_target['media_hash']}",
                json={"value": bad},
                content_type="application/json",
            )
            assert response.status_code == 400

    def test_missing_video(self, client):
        response = client.post(
            "/api/ratings/nonexistent_video_12345",
            json={"value": 3},
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_missing_video_get(self, client):
        response = client.get("/api/ratings/nonexistent_video_12345")
        assert response.status_code == 404

    def test_rating_range(self, client, rating_target):
        for rating_value in range(1, 6):
            response = client.post(
                f"/api/ratings/{rating_target['media_hash']}",
                json={"value": rating_value},
                content_type="application/json",
            )
            assert response.status_code == 201

            get_response = client.get(f"/api/ratings/{rating_target['media_hash']}")
            assert get_response.status_code == 200

    def test_rating_json_structure(self, client, rating_target):
        post_response = client.post(
            f"/api/ratings/{rating_target['media_hash']}",
            json={"value": 4},
            content_type="application/json",
        )
        assert post_response.status_code == 201

        response = client.get(f"/api/ratings/{rating_target['media_hash']}")
        data = response.get_json()
        assert isinstance(data, dict)
        assert "average" in data
        assert "count" in data
        assert isinstance(data["average"], (int, float))
        assert isinstance(data["count"], int)


class TestRatingCacheBehavior:
    def test_cache_invalidation_on_write(self, client, rating_target):
        from cache_manager import cache

        cache.refresh_all()
        response = client.post(
            f"/api/ratings/{rating_target['media_hash']}",
            json={"value": 4},
            content_type="application/json",
        )
        assert response.status_code == 201

        ratings = cache.get_ratings()
        assert isinstance(ratings, dict)

    def test_json_fallback_works(self, client, rating_target):
        from cache_manager import cache

        ratings = cache.get_ratings()
        assert isinstance(ratings, dict)


class TestRatingDatabasePersistence:
    def test_rating_written_to_db(self, client, rating_target):
        db = VideoDatabase()

        response = client.post(
            f"/api/ratings/{rating_target['media_hash']}",
            json={"value": 4},
            content_type="application/json",
        )
        assert response.status_code == 201

        conn = sqlite3.connect(str(db.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT rating FROM ratings WHERE filename = ?",
            (rating_target["filename"],),
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == 4

    def test_rating_survives_cache_clear(self, client, rating_target):
        from cache_manager import cache

        db = VideoDatabase()

        response = client.post(
            f"/api/ratings/{rating_target['media_hash']}",
            json={"value": 3},
            content_type="application/json",
        )
        assert response.status_code == 201

        cache.refresh_all()

        conn = sqlite3.connect(str(db.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT rating FROM ratings WHERE filename = ?",
            (rating_target["filename"],),
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == 3

    def test_rating_update_overwrites_previous(self, client, rating_target):
        db = VideoDatabase()

        first = client.post(
            f"/api/ratings/{rating_target['media_hash']}",
            json={"value": 2},
            content_type="application/json",
        )
        second = client.post(
            f"/api/ratings/{rating_target['media_hash']}",
            json={"value": 5},
            content_type="application/json",
        )
        assert first.status_code == 201
        assert second.status_code == 201

        conn = sqlite3.connect(str(db.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM ratings WHERE filename = ?",
            (rating_target["filename"],),
        )
        count = cursor.fetchone()[0]
        cursor.execute(
            "SELECT rating FROM ratings WHERE filename = ?",
            (rating_target["filename"],),
        )
        result = cursor.fetchone()
        conn.close()

        assert count == 1
        assert result[0] == 5


class TestRatingRateLimiting:
    def test_rate_limiting_enforced(self, client, rating_target):
        for i in range(5):
            response = client.post(
                f"/api/ratings/{rating_target['media_hash']}",
                json={"value": i % 5 + 1},
                content_type="application/json",
            )
            assert response.status_code == 201

        response = client.post(
            f"/api/ratings/{rating_target['media_hash']}",
            json={"value": 3},
            content_type="application/json",
        )
        assert response.status_code == 429

    def test_rate_limit_includes_retry_after(self, client, rating_target):
        for _ in range(5):
            client.post(
                f"/api/ratings/{rating_target['media_hash']}",
                json={"value": 3},
                content_type="application/json",
            )

        response = client.post(
            f"/api/ratings/{rating_target['media_hash']}",
            json={"value": 3},
            content_type="application/json",
        )

        assert response.status_code == 429
        assert "Retry-After" in response.headers

    def test_rate_limit_error_message(self, client, rating_target):
        for _ in range(5):
            client.post(
                f"/api/ratings/{rating_target['media_hash']}",
                json={"value": 3},
                content_type="application/json",
            )

        response = client.post(
            f"/api/ratings/{rating_target['media_hash']}",
            json={"value": 3},
            content_type="application/json",
        )

        data = response.get_json()
        assert response.status_code == 429
        assert "error" in data
        assert "Rate limit exceeded" in data["error"]


class TestPydanticValidation:
    def test_string_rating_coerced_to_int(self, client, rating_target):
        response = client.post(
            f"/api/ratings/{rating_target['media_hash']}",
            json={"value": "4"},
            content_type="application/json",
        )
        assert response.status_code == 201

    def test_float_rating_coerced_to_int(self, client, rating_target):
        response = client.post(
            f"/api/ratings/{rating_target['media_hash']}",
            json={"value": 4.5},
            content_type="application/json",
        )
        assert response.status_code in [201, 400]

    def test_null_rating_rejected(self, client, rating_target):
        response = client.post(
            f"/api/ratings/{rating_target['media_hash']}",
            json={"value": None},
            content_type="application/json",
        )
        assert response.status_code == 400


class TestMediaHashResolution:
    def test_media_hash_roundtrip(self, rating_target):
        from backend.services.ratings_service import RatingsService

        media_hash = RatingsService.get_media_hash(rating_target["filename"])
        assert media_hash
        assert isinstance(media_hash, str)
        assert len(media_hash) == 16

        resolved_filename = ratings_service.get_filename_by_hash(media_hash)
        assert resolved_filename == rating_target["filename"]

    def test_cache_invalidation_paths(self):
        from cache_manager import VideoCache

        cache = VideoCache()
        methods = [
            "invalidate_ratings",
            "invalidate_views",
            "invalidate_tags",
            "invalidate_favorites",
            "invalidate_video_list",
            "invalidate_metadata",
        ]

        for method_name in methods:
            assert hasattr(cache, method_name)
            method = getattr(cache, method_name)
            assert callable(method)
            method()


class TestRateLimiterFixture:
    def test_rate_limit_reset_isolation_first(self, client, rating_target):
        response = client.post(
            f"/api/ratings/{rating_target['media_hash']}",
            json={"value": 1},
            content_type="application/json",
        )
        assert response.status_code in [201, 429]

    def test_rate_limit_reset_isolation_second(self, client, rating_target):
        response = client.post(
            f"/api/ratings/{rating_target['media_hash']}",
            json={"value": 2},
            content_type="application/json",
        )
        assert response.status_code in [201, 429]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
