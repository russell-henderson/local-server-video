"""
tests/test_rating_mapping.py

Unit tests for API value -> database rating mapping.
"""

from __future__ import annotations

from pathlib import Path
import tempfile
from uuid import uuid4

import pytest

from backend.app.api.ratings import ratings_service


@pytest.fixture
def real_video_file():
    """Create temporary backing video file for service-level set_rating checks."""
    videos_dir = Path("videos")
    videos_dir.mkdir(parents=True, exist_ok=True)
    filename = f"phase8_map_{uuid4().hex}.mp4"
    path = videos_dir / filename
    path.write_bytes(b"\x00")
    try:
        yield filename
    finally:
        path.unlink(missing_ok=True)


class TestRatingColumnMapping:
    def test_value_to_rating_mapping(self):
        import os

        from backend.services.ratings_service import RatingsService
        from cache_manager import VideoCache
        from database_migration import VideoDatabase

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = VideoDatabase(db_path=db_path)
            cache = VideoCache()
            service = RatingsService(cache, db)

            test_filename = "test_video.mp4"
            with db.get_connection() as conn:
                conn.execute("INSERT INTO videos (filename) VALUES (?)", (test_filename,))
                conn.execute(
                    "INSERT OR REPLACE INTO ratings (filename, rating) VALUES (?, ?)",
                    (test_filename, 4),
                )
                conn.commit()

            service.register_media_hash(test_filename)
            with db.get_connection() as conn:
                row = conn.execute(
                    "SELECT rating FROM ratings WHERE filename = ?",
                    (test_filename,),
                ).fetchone()

            assert row is not None
            assert row["rating"] == 4

    def test_api_payload_validation(self, real_video_file):
        import os

        from backend.services.ratings_service import RatingsService
        from cache_manager import VideoCache
        from database_migration import VideoDatabase

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = VideoDatabase(db_path=db_path)
            cache = VideoCache()
            service = RatingsService(cache, db)

            with db.get_connection() as conn:
                conn.execute("INSERT INTO videos (filename) VALUES (?)", (real_video_file,))
                conn.commit()

            media_hash = service.register_media_hash(real_video_file)

            for value in [1, 2, 3, 4, 5]:
                result = service.set_rating(media_hash, value)
                assert result is not None

            for value in [0, 6, -1, 10]:
                with pytest.raises(ValueError, match="Rating must be 1-5"):
                    service.set_rating(media_hash, value)

    def test_rating_summary_structure(self, real_video_file):
        from database_migration import VideoDatabase

        db = VideoDatabase()
        media_hash = ratings_service.register_media_hash(real_video_file)
        with db.get_connection() as conn:
            conn.execute("DELETE FROM ratings WHERE filename = ?", (real_video_file,))
            conn.commit()

        summary = ratings_service.get_rating_summary(media_hash)
        assert "average" in summary
        assert "count" in summary
        assert "user" in summary
        assert summary["user"] is None

        ratings_service.set_rating(media_hash, 3)
        summary = ratings_service.get_rating_summary(media_hash)
        assert summary["user"] is not None
        assert summary["user"]["value"] == 3
        assert summary["average"] == 3.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
