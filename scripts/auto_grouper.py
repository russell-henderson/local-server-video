import sqlite3
import sys
import re
from pathlib import Path

def auto_grouper():
    db_path = Path('data/video_metadata.db')
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        sys.exit(1)

    # Phase A: Define Group Targets & Rules
    groups_config = {
        'Motion': {'ext': ['.gif', '.webp']},
        'Blonde': {'keywords': ['blonde', 'blond']},
        'Brunette': {'keywords': ['brunette']},
        'Redhead': {'keywords': ['redhead', 'red hair', 'ginger']},
        'Dark Hair': {'keywords': ['dark hair', 'black hair', 'raven']}
    }

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Phase B: Execute Database Transaction Loops
        
        # 1. Upsert Groups
        group_ids = {}
        for group_name in groups_config.keys():
            # Create slug for the group (standard in this schema)
            slug = group_name.lower().replace(' ', '-')
            cursor.execute(
                "INSERT OR IGNORE INTO gallery_groups (name, slug) VALUES (?, ?)",
                (group_name, slug)
            )
            # Retrieve ID
            cursor.execute("SELECT id FROM gallery_groups WHERE name = ?", (group_name,))
            group_ids[group_name] = cursor.fetchone()['id']
        
        # 2. Map Items
        cursor.execute("SELECT filename FROM videos")
        videos = cursor.fetchall()
        
        batch_items = []
        counts = {name: 0 for name in groups_config.keys()}
        
        for video in videos:
            filename = video['filename']
            assigned_group = None
            
            # Rule 1: Motion Rule
            if any(filename.lower().endswith(ext) for ext in groups_config['Motion']['ext']):
                assigned_group = 'Motion'
            else:
                # Rule 2: Hair Color Classification
                fn_lower = filename.lower()
                for group_name, config in groups_config.items():
                    if group_name == 'Motion': continue
                    if any(keyword in fn_lower for keyword in config['keywords']):
                        assigned_group = group_name
                        break
            
            if assigned_group:
                # Prepare for batch insertion into gallery_group_items
                # Note: position is optional but good practice to keep consistent
                batch_items.append((group_ids[assigned_group], filename))
                counts[assigned_group] += 1

        # 3. Batch Insertion
        if batch_items:
            # We use INSERT OR IGNORE to prevent uniqueness constraint faults (group_id, image_path)
            # Checking if a unique constraint exists on (group_id, image_path)
            # PRAGMA index_list(gallery_group_items) would tell us, but INSERT OR IGNORE is safe anyway.
            cursor.executemany(
                "INSERT OR IGNORE INTO gallery_group_items (group_id, image_path) VALUES (?, ?)",
                batch_items
            )
            conn.commit()
            
        # Phase C: Output & Summary Status
        print("=== Automated Gallery Grouper Summary ===")
        for group_name, count in counts.items():
            print(f"Group '{group_name}': {count} files routed")
        print(f"Total files assigned to groups: {len(batch_items)}")
        print("==========================================")

    except Exception as e:
        print(f"An error occurred during grouping: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    auto_grouper()
