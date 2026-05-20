"""
Admin Operations Engine
Handles physical file management and atomic SQLite metadata state changes across all tables.
"""
import os
import shutil
import sqlite3
from pathlib import Path
from typing import Dict, Any

class AdminMediaManager:
    def __init__(self, db_path: str = "data/video_metadata.db", storage_root: str = "/app/videos"):
        self.db_path = db_path
        self.storage_root = Path(storage_root)

    def _get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def rename_media(self, old_filename: str, new_filename: str) -> Dict[str, Any]:
        """Renames a file on disk and updates all metadata table references atomically."""
        old_path = self.storage_root / old_filename
        new_path = self.storage_root / new_filename

        if not old_path.exists():
            raise FileNotFoundError(f"Source media '{old_filename}' does not exist on disk.")
        if new_path.exists():
            raise FileExistsError(f"Target media destination '{new_filename}' is already occupied.")

        # Execute physical disk rename
        shutil.move(str(old_path), str(new_path))

        conn = self._get_db_connection()
        try:
            with conn:
                # Synchronize across all known metadata tables targeting the filename
                conn.execute("UPDATE videos SET filename = ? WHERE filename = ?", (new_filename, old_filename))
                conn.execute("UPDATE ratings SET filename = ? WHERE filename = ?", (new_filename, old_filename))
                conn.execute("UPDATE views SET filename = ? WHERE filename = ?", (new_filename, old_filename))
                conn.execute("UPDATE video_tags SET filename = ? WHERE filename = ?", (new_filename, old_filename))
                conn.execute("UPDATE favorites SET filename = ? WHERE filename = ?", (new_filename, old_filename))
                
                # gallery_group_items uses 'image_path' as the filename column
                conn.execute("UPDATE gallery_group_items SET image_path = ? WHERE image_path = ?", (new_filename, old_filename))
                
                # Additional system tables that track filenames
                conn.execute("UPDATE media_hash_map SET filename = ? WHERE filename = ?", (new_filename, old_filename))
                conn.execute("UPDATE phash_cache SET filename = ? WHERE filename = ?", (new_filename, old_filename))
                
            return {"success": True, "message": f"Successfully shifted tracking to {new_filename}."}
        except sqlite3.Error as e:
            shutil.move(str(new_path), str(old_path))
            raise RuntimeError(f"Database sync failed; file operation rolled back: {str(e)}")
        finally:
            conn.close()

    def duplicate_media(self, source_filename: str, dest_filename: str) -> Dict[str, Any]:
        """Copies physical media and clones its associated metadata payload across all related tables."""
        source_path = self.storage_root / source_filename
        dest_path = self.storage_root / dest_filename

        if not source_path.exists():
            raise FileNotFoundError(f"Source media '{source_filename}' does not exist.")
        if dest_path.exists():
            raise FileExistsError(f"Destination path '{dest_filename}' already contains media.")

        # Execute physical duplication
        shutil.copy2(str(source_path), str(dest_path))

        conn = self._get_db_connection()
        try:
            with conn:
                # 1. Clone base video metadata row
                row = conn.execute("SELECT * FROM videos WHERE filename = ?", (source_filename,)).fetchone()
                if row:
                    data = dict(row)
                    data['filename'] = dest_filename
                    if 'id' in data: del data['id']
                    fields = ", ".join(data.keys())
                    placeholders = ", ".join(["?"] * len(data))
                    conn.execute(f"INSERT INTO videos ({fields}) VALUES ({placeholders})", list(data.values()))

                # 2. Duplicate associated sub-metadata elements dynamically
                metadata_tables = {
                    'ratings': 'filename',
                    'views': 'filename',
                    'video_tags': 'filename',
                    'favorites': 'filename',
                    'gallery_group_items': 'image_path',
                    'media_hash_map': 'filename',
                    'phash_cache': 'filename'
                }
                
                for table, col in metadata_tables.items():
                    rows = conn.execute(f"SELECT * FROM {table} WHERE {col} = ?", (source_filename,)).fetchall()
                    for r in rows:
                        data = dict(r)
                        data[col] = dest_filename
                        if 'id' in data: del data['id']
                        fields = ", ".join(data.keys())
                        placeholders = ", ".join(["?"] * len(data))
                        conn.execute(f"INSERT INTO {table} ({fields}) VALUES ({placeholders})", list(data.values()))
                    
            return {"success": True, "message": f"Successfully cloned data assets to {dest_filename}."}
        except sqlite3.Error as e:
            if dest_path.exists(): os.remove(dest_path)
            raise RuntimeError(f"Database cloning transaction failed; removed duplicated file: {str(e)}")
        finally:
            conn.close()
