import os
import json
import tempfile
from pathlib import Path
import shutil

import pytest

# Ensure project root is importable
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))

from cache_manager import VideoCache


def setup_temp_videos_dir(tmp_path):
    videos_dir = tmp_path / "videos"
    videos_dir.mkdir()
    # create a fake video file
    vid = videos_dir / "sample.mp4"
    vid.write_text("fake")
    return str(videos_dir)


def test_favorites_and_views_json_backend(tmp_path, monkeypatch):
    # Create temporary videos dir and JSON files
    videos_dir = setup_temp_videos_dir(tmp_path)

    # Monkeypatch file paths used by VideoCache
    cache = VideoCache(cache_ttl=1, use_database=False)
    cache.video_dir = videos_dir
    cache.ratings_file = str(tmp_path / "ratings.json")
    cache.views_file = str(tmp_path / "views.json")
    cache.tags_file = str(tmp_path / "tags.json")
    cache.favorites_file = str(tmp_path / "favorites.json")

    # Ensure starting state
    assert cache.get_video_list() == ["sample.mp4"]
    assert cache.get_favorites() == []

    # Toggle favorite by updating directly
    cache.update_favorites(["sample.mp4"])
    assert "sample.mp4" in cache.get_favorites()

    # Increment view
    new_views = cache.update_view("sample.mp4")
    assert isinstance(new_views, int)
    views = cache.get_views()
    assert views.get("sample.mp4", 0) == new_views

    # Clean up
    shutil.rmtree(videos_dir, ignore_errors=True)
