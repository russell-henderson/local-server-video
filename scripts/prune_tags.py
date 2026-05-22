import sqlite3
import sys
from pathlib import Path

def prune_tags():
    db_path = Path('data/video_metadata.db')
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        sys.exit(1)

    # Step A: Define the Blacklist Array
    blacklist = [
        # Contractions/Pronouns
        'cant', 'wont', 'dont', 'shant', 'your', 'that', 'this', 'what', 'when', 'where', 'with', 'from', 'them', 'they',
        # Verbs/Misc
        'get', 'has', 'had', 'was', 'are', 'the', 'and', 'for', 'but', 'not', 'you', 'him', 'her', 'who', 'how', 'why'
    ]

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Step B: Execute the Delete Transaction
        # We use a transaction to ensure atomicity.
        # The query specifically targets the blacklist. 
        # Safety check: Performer tags (hyphenated) and studio tags (not in blacklist) are naturally preserved.
        
        print(f"Pruning {len(blacklist)} unique low-value terms from video_tags...")
        
        cursor.execute("SELECT COUNT(*) FROM video_tags")
        before_count = cursor.fetchone()[0]

        placeholders = ', '.join(['?'] * len(blacklist))
        query = f"DELETE FROM video_tags WHERE tag IN ({placeholders})"
        
        cursor.execute(query, blacklist)
        conn.commit()
        
        deleted_count = cursor.rowcount
        
        cursor.execute("SELECT COUNT(*) FROM video_tags")
        after_count = cursor.fetchone()[0]

        # Step C: Terminal Reporting
        print("=== Tag Pruning Execution Summary ===")
        print(f"Total tags before pruning: {before_count}")
        print(f"Total low-value records deleted: {deleted_count}")
        print(f"Total tags remaining: {after_count}")
        print("======================================")

    except Exception as e:
        print(f"An error occurred during pruning: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    prune_tags()
