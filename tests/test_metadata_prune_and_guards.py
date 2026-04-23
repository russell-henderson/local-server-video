import tempfile
from pathlib import Path

import main
from cache_manager import VideoCache


def _setup_temp_json_cache(monkeypatch):
    td = tempfile.TemporaryDirectory()
    root = Path(td.name)
    videos_dir = root / "videos"
    videos_dir.mkdir(parents=True, exist_ok=True)

    valid_file = videos_dir / "sample.mp4"
    valid_file.write_text("fake-video", encoding="utf-8")

    cache = VideoCache(cache_ttl=1, use_database=False)
    cache.video_dir = str(videos_dir)
    cache.ratings_file = str(root / "ratings.json")
    cache.views_file = str(root / "views.json")
    cache.tags_file = str(root / "tags.json")
    cache.favorites_file = str(root / "favorites.json")
    cache.refresh_all()

    monkeypatch.setattr(main, "cache", cache)
    monkeypatch.setattr(main, "VIDEO_DIR", videos_dir)
    return td, cache


def test_filename_guards_for_write_endpoints(client, monkeypatch):
    td, _ = _setup_temp_json_cache(monkeypatch)
    try:
        guarded_routes = ["/rate", "/view", "/tag", "/delete_tag", "/favorite"]

        # Blank filename should be rejected consistently.
        for route in guarded_routes:
            payload = {"filename": " "}
            if route == "/rate":
                payload["rating"] = 3
            if route in {"/tag", "/delete_tag"}:
                payload["tag"] = "#test"

            resp = client.post(route, json=payload)
            assert resp.status_code == 400
            assert resp.get_json().get("error") == "Missing filename"

        # Missing-on-disk filename should return 404.
        for route in guarded_routes:
            payload = {"filename": "__missing__.mp4"}
            if route == "/rate":
                payload["rating"] = 3
            if route in {"/tag", "/delete_tag"}:
                payload["tag"] = "#test"

            resp = client.post(route, json=payload)
            assert resp.status_code == 404
            assert resp.get_json().get("error") == "Video not found"
    finally:
        td.cleanup()


def test_valid_filename_succeeds_for_write_endpoints(client, monkeypatch):
    td, _ = _setup_temp_json_cache(monkeypatch)
    try:
        filename = "sample.mp4"

        rate = client.post("/rate", json={"filename": filename, "rating": 4})
        assert rate.status_code == 200
        assert rate.get_json().get("success") is True

        view = client.post("/view", json={"filename": filename})
        assert view.status_code == 200
        assert view.get_json().get("success") is True

        add_tag = client.post("/tag", json={"filename": filename, "tag": "guard-ok"})
        assert add_tag.status_code == 200
        assert add_tag.get_json().get("success") is True

        delete_tag = client.post("/delete_tag", json={"filename": filename, "tag": "#guard-ok"})
        assert delete_tag.status_code == 200
        assert delete_tag.get_json().get("success") is True

        favorite = client.post("/favorite", json={"filename": filename})
        assert favorite.status_code == 200
        assert favorite.get_json().get("success") is True
    finally:
        td.cleanup()


def test_admin_metadata_prune_removes_only_stale_and_is_idempotent(client, monkeypatch):
    td, cache = _setup_temp_json_cache(monkeypatch)
    try:
        valid_filename = "sample.mp4"
        stale_filename = "__stale__.mp4"

        # Seed valid metadata that must survive prune.
        cache.update_rating(valid_filename, 5)
        cache.update_view(valid_filename)
        cache.update_tags(valid_filename, ["#valid-tag"])
        cache.update_favorites([valid_filename])

        # Seed stale metadata that should be removed by prune.
        cache.update_rating(stale_filename, 2)
        cache.update_view(stale_filename)
        cache.update_tags(stale_filename, ["#stale-tag"])
        cache.update_favorites([valid_filename, stale_filename])

        first = client.post("/admin/metadata/prune")
        assert first.status_code == 200
        payload = first.get_json()
        assert payload.get("success") is True
        assert payload.get("ratings_removed") == 1
        assert payload.get("views_removed") == 1
        assert payload.get("favorites_removed") == 1
        assert payload.get("tag_entries_removed") == 1
        assert payload.get("tag_values_removed") == 1

        # Stale rows are gone; valid rows remain.
        assert stale_filename not in cache.get_ratings()
        assert stale_filename not in cache.get_views()
        assert stale_filename not in cache.get_tags()
        assert stale_filename not in cache.get_favorites()

        assert valid_filename in cache.get_ratings()
        assert valid_filename in cache.get_views()
        assert valid_filename in cache.get_tags()
        assert valid_filename in cache.get_favorites()

        # Second run should be idempotent.
        second = client.post("/admin/metadata/prune")
        assert second.status_code == 200
        payload2 = second.get_json()
        assert payload2.get("ratings_removed") == 0
        assert payload2.get("views_removed") == 0
        assert payload2.get("favorites_removed") == 0
        assert payload2.get("tag_entries_removed") == 0
        assert payload2.get("tag_values_removed") == 0
    finally:
        td.cleanup()
