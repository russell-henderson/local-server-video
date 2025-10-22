"""Standalone smoke test for favorites and views using JSON backend
Run with: python tests/run_fav_views_smoke.py
"""
import tempfile
from pathlib import Path
import sys

# Ensure project root importable
sys.path.insert(0, str(Path(__file__).parents[1]))

from cache_manager import VideoCache


def run():
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        videos_dir = td_path / "videos"
        videos_dir.mkdir()
        sample = videos_dir / "sample.mp4"
        sample.write_text("fake")

        cache = VideoCache(cache_ttl=1, use_database=False)

        # Point cache to temp paths BEFORE forcing a reload
        cache.video_dir = str(videos_dir)
        cache.ratings_file = str(td_path / "ratings.json")
        cache.views_file = str(td_path / "views.json")
        cache.tags_file = str(td_path / "tags.json")
        cache.favorites_file = str(td_path / "favorites.json")

        # Force video_list to refresh from the new directory
        cache._last_refresh['video_list'] = 0
        video_list = cache.get_video_list()
        print("Video list:", video_list)
        assert video_list == ["sample.mp4"], "video discovery failed"

        favs = cache.get_favorites()
        print("Initial favorites:", favs)
        assert favs == [], "favorites should start empty"

        cache.update_favorites(["sample.mp4"])
        favs2 = cache.get_favorites()
        print("After update favorites:", favs2)
        assert "sample.mp4" in favs2, "favorite update failed"

        new_views = cache.update_view("sample.mp4")
        print("New views count:", new_views)
        views = cache.get_views()
        print("Views dict:", views)
        assert views.get("sample.mp4", 0) == new_views, "view update failed"

        print("All smoke checks passed")


if __name__ == '__main__':
    try:
        run()
        print('SMOKE TEST: PASS')
    except AssertionError as e:
        print('SMOKE TEST: FAIL:', e)
        raise
    except Exception as ex:
        print('SMOKE TEST: ERROR:', ex)
        raise
