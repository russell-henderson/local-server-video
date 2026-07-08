"""
Playlists Service
Handles transactional SQLite operations for explicit static playlists.
"""
import sqlite3
from typing import List, Dict, Optional, Any
from backend.app.core.db import get_db_session

SPOTLIGHT_ACTIONS = {"continue", "shuffle", "newest", "highest_rated", "custom"}
SORT_MODES = {"manual", "name", "created_at", "rating", "views"}


class PlaylistsService:
    def __init__(self):
        self.db = get_db_session()

    def normalize_playlist(self, raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Return a playlist dict with additive metadata defaults."""
        playlist = dict(raw or {})
        playlist.setdefault("description", None)
        playlist.setdefault("cover_image", None)
        playlist.setdefault("spotlight_label", "")
        playlist.setdefault("spotlight_action", "continue")
        playlist.setdefault("spotlight_enabled", True)
        playlist.setdefault("sort_mode", "manual")
        playlist.setdefault("autoplay_enabled", True)
        playlist.setdefault("autoplay_next", False)
        playlist.setdefault("shuffle_default", False)
        playlist.setdefault("last_played_video", None)
        playlist.setdefault("last_opened_at", None)
        playlist.setdefault("updated_at", None)
        playlist.setdefault("videos", [])
        playlist.setdefault("items", [])
        if playlist.get("spotlight_action") not in SPOTLIGHT_ACTIONS:
            playlist["spotlight_action"] = "continue"
        if playlist.get("sort_mode") not in SORT_MODES:
            playlist["sort_mode"] = "manual"
        if playlist.get("spotlight_label") is None:
            playlist["spotlight_label"] = ""
        if playlist.get("spotlight_enabled") is None:
            playlist["spotlight_enabled"] = True
        else:
            playlist["spotlight_enabled"] = bool(playlist.get("spotlight_enabled"))
        if playlist.get("autoplay_enabled") is None:
            playlist["autoplay_enabled"] = True
        else:
            playlist["autoplay_enabled"] = bool(playlist.get("autoplay_enabled"))
        playlist["autoplay_next"] = bool(playlist.get("autoplay_next"))
        playlist["shuffle_default"] = bool(playlist.get("shuffle_default"))
        return playlist

    def _playlist_exists(self, conn, playlist_id: int) -> bool:
        row = conn.execute("SELECT 1 FROM playlists WHERE id = ?", (playlist_id,)).fetchone()
        return row is not None

    def create_playlist(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new explicit static playlist."""
        try:
            with self.db.get_session() as conn:
                cursor = conn.execute(
                    "INSERT INTO playlists (name, description) VALUES (?, ?)",
                    (name, description)
                )
                playlist_id = cursor.lastrowid
                conn.commit()
                return {
                    "success": True,
                    "playlist_id": playlist_id,
                    "name": name,
                    "description": description
                }
        except sqlite3.IntegrityError:
            return {"success": False, "error": "Playlist name must be unique."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_playlist(self, playlist_id: int) -> Dict[str, Any]:
        """Delete a playlist and all its items (handled by CASCADE)."""
        try:
            with self.db.get_session() as conn:
                conn.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
                conn.commit()
                return {"success": True, "message": f"Playlist {playlist_id} deleted."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def add_to_playlist(self, playlist_id: int, video_filename: str) -> Dict[str, Any]:
        """Append a video to a playlist, handling positioning automatically."""
        try:
            with self.db.get_session() as conn:
                # Get current max position
                cursor = conn.execute(
                    "SELECT MAX(position) FROM playlist_items WHERE playlist_id = ?",
                    (playlist_id,)
                )
                row = cursor.fetchone()
                next_position = (row[0] + 1) if (row and row[0] is not None) else 0

                conn.execute(
                    "INSERT INTO playlist_items (playlist_id, video_filename, position) VALUES (?, ?, ?)",
                    (playlist_id, video_filename, next_position)
                )
                conn.commit()
                return {"success": True, "message": f"Added {video_filename} to playlist {playlist_id} at position {next_position}."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def remove_from_playlist(self, playlist_id: int, video_filename: str, position: Optional[int] = None) -> Dict[str, Any]:
        """Remove a video from a playlist and re-order remaining items."""
        try:
            with self.db.get_session() as conn:
                if position is not None:
                    conn.execute(
                        "DELETE FROM playlist_items WHERE playlist_id = ? AND video_filename = ? AND position = ?",
                        (playlist_id, video_filename, position)
                    )
                else:
                    conn.execute(
                        "DELETE FROM playlist_items WHERE playlist_id = ? AND video_filename = ?",
                        (playlist_id, video_filename)
                    )
                
                # Re-order remaining items to maintain sequential gap-less numbering
                rows = conn.execute(
                    "SELECT id FROM playlist_items WHERE playlist_id = ? ORDER BY position ASC",
                    (playlist_id,)
                ).fetchall()
                
                for idx, row in enumerate(rows):
                    conn.execute(
                        "UPDATE playlist_items SET position = ? WHERE id = ?",
                        (idx, row['id'])
                    )
                
                conn.commit()
                return {"success": True, "message": f"Removed {video_filename} from playlist {playlist_id}."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_playlists(self) -> List[Dict[str, Any]]:
        """Retrieve all playlists."""
        with self.db.get_session() as conn:
            cursor = conn.execute(
                "SELECT * FROM playlists ORDER BY name ASC"
            )
            return [self.normalize_playlist(dict(row)) for row in cursor.fetchall()]

    def get_playlist_queue(self, playlist_id: int) -> Dict[str, Any]:
        """Retrieve the sequential video queue for a playlist."""
        with self.db.get_session() as conn:
            conn.execute(
                "UPDATE playlists SET last_opened_at = CURRENT_TIMESTAMP WHERE id = ?",
                (playlist_id,)
            )
            conn.commit()
            playlist_row = conn.execute(
                "SELECT * FROM playlists WHERE id = ?", (playlist_id,)
            ).fetchone()
            
            if not playlist_row:
                return {"success": False, "error": "Playlist not found."}

            cursor = conn.execute("""
                SELECT pi.video_filename, pi.position, v.duration, v.added_date
                FROM playlist_items pi
                JOIN videos v ON pi.video_filename = v.filename
                WHERE pi.playlist_id = ?
                ORDER BY pi.position ASC
            """, (playlist_id,))
            
            items = [dict(row) for row in cursor.fetchall()]
            
            result = dict(playlist_row)
            result['items'] = items
            result['success'] = True
            return self.normalize_playlist(result)

    def get_playlist(self, playlist_id: int) -> Dict[str, Any]:
        with self.db.get_session() as conn:
            row = conn.execute("SELECT * FROM playlists WHERE id = ?", (playlist_id,)).fetchone()
            if not row:
                return {"success": False, "error": "Playlist not found."}
            result = self.normalize_playlist(dict(row))
            result["success"] = True
            return result

    def update_metadata(self, playlist_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Update editable playlist metadata only."""
        allowed = {
            "name", "description", "spotlight_label", "spotlight_action",
            "spotlight_enabled", "sort_mode", "autoplay_enabled",
            "autoplay_next", "shuffle_default",
        }
        updates: Dict[str, Any] = {}

        for key, value in (payload or {}).items():
            if key not in allowed:
                continue
            if key in {"name", "description", "spotlight_label", "spotlight_action", "sort_mode"}:
                value = "" if value is None else str(value).strip()
            if key == "name" and not value:
                return {"success": False, "error": "Playlist name is required."}
            if key == "description" and len(value) > 500:
                return {"success": False, "error": "Description must be 500 characters or less."}
            if key == "spotlight_label" and len(value) > 80:
                return {"success": False, "error": "Spotlight label must be 80 characters or less."}
            if key == "spotlight_action" and value not in SPOTLIGHT_ACTIONS:
                return {"success": False, "error": "Unknown spotlight action."}
            if key == "sort_mode" and value not in SORT_MODES:
                return {"success": False, "error": "Unknown sort mode."}
            if key in {"spotlight_enabled", "autoplay_enabled", "autoplay_next", "shuffle_default"}:
                value = 1 if bool(value) else 0
            updates[key] = value

        if not updates:
            return self.get_playlist(playlist_id)

        try:
            with self.db.get_session() as conn:
                if not self._playlist_exists(conn, playlist_id):
                    return {"success": False, "error": "Playlist not found."}
                assignments = ", ".join(f"{key} = ?" for key in updates)
                values = list(updates.values()) + [playlist_id]
                conn.execute(
                    f"UPDATE playlists SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    values,
                )
                conn.commit()
            return self.get_playlist(playlist_id)
        except sqlite3.IntegrityError:
            return {"success": False, "error": "Playlist name must be unique."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_cover(self, playlist_id: int, cover_image: Optional[str]) -> Dict[str, Any]:
        try:
            with self.db.get_session() as conn:
                if not self._playlist_exists(conn, playlist_id):
                    return {"success": False, "error": "Playlist not found."}
                conn.execute(
                    "UPDATE playlists SET cover_image = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (cover_image, playlist_id),
                )
                conn.commit()
            return self.get_playlist(playlist_id)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_summary(self) -> Dict[str, Any]:
        with self.db.get_session() as conn:
            playlists = self.get_playlists()
            counts = {}
            for row in conn.execute(
                "SELECT playlist_id, COUNT(*) AS count FROM playlist_items GROUP BY playlist_id"
            ):
                counts[row["playlist_id"]] = row["count"]

            total_videos = sum(counts.values())
            largest = None
            for playlist in playlists:
                count = counts.get(playlist["id"], 0)
                if largest is None or count > largest["count"]:
                    largest = {"id": playlist["id"], "name": playlist["name"], "count": count}

            recent_rows = conn.execute(
                """
                SELECT id, name, last_opened_at FROM playlists
                WHERE last_opened_at IS NOT NULL
                ORDER BY last_opened_at DESC
                LIMIT 3
                """
            ).fetchall()

        return {
            "success": True,
            "total_playlists": len(playlists),
            "total_videos": total_videos,
            "largest_playlist": largest,
            "recently_opened": [dict(row) for row in recent_rows],
            "popular_tags": [],
        }
