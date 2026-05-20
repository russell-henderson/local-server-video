"""
Playlists Service
Handles transactional SQLite operations for explicit static playlists.
"""
import sqlite3
from typing import List, Dict, Optional, Any
from backend.app.core.db import get_db_session

class PlaylistsService:
    def __init__(self):
        self.db = get_db_session()

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
                "SELECT id, name, description, created_at FROM playlists ORDER BY name ASC"
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_playlist_queue(self, playlist_id: int) -> Dict[str, Any]:
        """Retrieve the sequential video queue for a playlist."""
        with self.db.get_session() as conn:
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
            return result
