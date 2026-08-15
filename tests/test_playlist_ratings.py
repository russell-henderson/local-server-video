import pytest
import sqlite3
import json
from backend.app.factory import create_app
from backend.app.services.playlists_service import PlaylistsService
from backend.app.core.db import get_db_session, _db_session
import backend.app.core.db as core_db
from database_migration import VideoDatabase
import os
import tempfile
import time

@pytest.fixture
def app_and_db():
    # Setup temporary database
    fd, temp_db = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.environ["LVS_DB_PATH"] = temp_db
    core_db._db_session = None # Reset global db session
    
    # Initialize DB
    db = VideoDatabase(temp_db)
    
    # Inject service into API module to avoid stale db references
    import backend.app.api.playlists as playlists_api
    playlists_api.service = PlaylistsService()
    
    app = create_app()
    app.config["TESTING"] = True
    
    # Add some dummy videos
    with db.get_connection() as conn:
        conn.execute("INSERT INTO videos (filename, added_date, file_size) VALUES ('video_A.mp4', ?, 1000)", (time.time(),))
        conn.execute("INSERT INTO videos (filename, added_date, file_size) VALUES ('video_B.mp4', ?, 1000)", (time.time(),))
        conn.execute("INSERT INTO ratings (filename, rating) VALUES ('video_A.mp4', 4)")
        conn.commit()
    
    yield app, db, temp_db
    
    # Teardown
    if os.path.exists(temp_db):
        os.remove(temp_db)

@pytest.fixture
def client(app_and_db):
    app, db, temp_db = app_and_db
    return app.test_client()

@pytest.fixture
def service():
    return PlaylistsService()

def test_video_rating_hydration(app_and_db, service):
    app, db, temp_db = app_and_db
    
    # Create playlist and add video
    with app.app_context():
        res = service.create_playlist("Test Playlist", "Desc")
        playlist_id = res["playlist_id"]
        
        service.add_to_playlist(playlist_id, "video_A.mp4")
        service.add_to_playlist(playlist_id, "video_B.mp4")
        
        # Get playlist queue
        queue = service.get_playlist_queue(playlist_id)
        assert queue["success"] is True
        
        items = queue["items"]
        assert len(items) == 2
        
        # Verify video_A has rating 4
        item_A = next(i for i in items if i["video_filename"] == "video_A.mp4")
        assert item_A["rating"] == 4
        
        # Verify video_B has rating 0 (null mapped to 0 usually in service)
        item_B = next(i for i in items if i["video_filename"] == "video_B.mp4")
        assert item_B["rating"] == 0

def test_video_rating_write_through(client, app_and_db, service, monkeypatch):
    app, db, temp_db = app_and_db
    
    # Mock legacy_runtime.get_video_path to pretend files exist
    import backend.app.legacy_runtime as legacy
    monkeypatch.setattr(legacy.Path, "exists", lambda self: True)
    
    with app.app_context():
        res = service.create_playlist("Test Playlist", "Desc")
        playlist_id = res["playlist_id"]
        service.add_to_playlist(playlist_id, "video_A.mp4")
        
        # Change video A rating directly in DB (simulating global rate)
        with db.get_connection() as conn:
            conn.execute("UPDATE ratings SET rating = 5 WHERE filename = 'video_A.mp4'")
            conn.commit()
            
        # Verify it reflects in playlist queue
        queue = service.get_playlist_queue(playlist_id)
        item_A = next(i for i in queue["items"] if i["video_filename"] == "video_A.mp4")
        assert item_A["rating"] == 5

def test_playlist_rating_persistence(client, app_and_db, service):
    app, db, temp_db = app_and_db
    
    with app.app_context():
        res = service.create_playlist("Test Playlist", "Desc")
        playlist_id = res["playlist_id"]
        
        # Initial playlist rating should be None
        playlist = service.get_playlist(playlist_id)
        assert playlist["rating"] is None
        
        # Rate playlist via API
        resp = client.post(f"/api/playlists/{playlist_id}/rating", json={"rating": 3})
        assert resp.status_code == 200
        
        # Verify reload/re-read preserves it
        playlist = service.get_playlist(playlist_id)
        assert playlist["rating"] == 3
        
def test_scope_isolation_A(client, app_and_db, service):
    app, db, temp_db = app_and_db
    
    with app.app_context():
        res = service.create_playlist("Test Playlist", "Desc")
        playlist_id = res["playlist_id"]
        service.add_to_playlist(playlist_id, "video_A.mp4")
        
        # Rate playlist 3
        client.post(f"/api/playlists/{playlist_id}/rating", json={"rating": 3})
        
        # Change playlist rating to 5
        client.post(f"/api/playlists/{playlist_id}/rating", json={"rating": 5})
        
        # Verify video A's rating remains 4
        with db.get_connection() as conn:
            r = conn.execute("SELECT rating FROM ratings WHERE filename = 'video_A.mp4'").fetchone()
            assert r["rating"] == 4

def test_scope_isolation_B(client, app_and_db, service, monkeypatch):
    app, db, temp_db = app_and_db
    
    import backend.app.legacy_runtime as legacy
    monkeypatch.setattr(legacy.Path, "exists", lambda self: True)
    
    with app.app_context():
        res = service.create_playlist("Test Playlist", "Desc")
        playlist_id = res["playlist_id"]
        service.add_to_playlist(playlist_id, "video_A.mp4")
        
        # Rate playlist 5
        client.post(f"/api/playlists/{playlist_id}/rating", json={"rating": 5})
        
        # Change video A's rating 4 -> 2 directly in DB
        with db.get_connection() as conn:
            conn.execute("UPDATE ratings SET rating = 2 WHERE filename = 'video_A.mp4'")
            conn.commit()
        
        # Verify playlist rating remains 5
        playlist = service.get_playlist(playlist_id)
        assert playlist["rating"] == 5

def test_existing_playlist_behavior(client, app_and_db, service):
    app, db, temp_db = app_and_db
    with app.app_context():
        # Create playlist
        resp = client.post("/api/playlists", json={"name": "New Playlist", "description": ""})
        assert resp.status_code == 201
        playlist_id = resp.json["playlist_id"]
        
        # Add items
        resp = client.post(f"/api/playlists/{playlist_id}/add", json={"video_filename": "video_A.mp4"})
        assert resp.status_code == 200
        
        resp = client.post(f"/api/playlists/{playlist_id}/add", json={"video_filename": "video_B.mp4"})
        assert resp.status_code == 200
        
        # Delete item
        resp = client.delete(f"/api/playlists/{playlist_id}/items/video_A.mp4")
        assert resp.status_code == 200
        
        # Verify only B remains
        queue = service.get_playlist_queue(playlist_id)
        assert len(queue["items"]) == 1
        assert queue["items"][0]["video_filename"] == "video_B.mp4"
        
        # Delete playlist
        resp = client.delete(f"/api/playlists/{playlist_id}")
        assert resp.status_code == 200
        assert service.get_playlist(playlist_id).get("success") is False
