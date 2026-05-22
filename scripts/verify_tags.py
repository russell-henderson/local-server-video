import sqlite3
import sys

def verify():
    conn = sqlite3.connect('data/video_metadata.db')
    cursor = conn.cursor()
    
    print("\n--- Performer Tags Verification ---")
    cursor.execute("SELECT filename, tag FROM video_tags WHERE tag LIKE '%-%' LIMIT 5")
    for row in cursor.fetchall():
        print(row)
        
    print("\n--- Studio Tags Verification ---")
    # Check for ANY tags that might be studios (not just the ones I listed)
    # But let's check the ones we specifically looked for
    cursor.execute("SELECT filename, tag FROM video_tags WHERE tag IN ('missax', 'blacked', 'tushy', 'vixen', 'pure-taboo') LIMIT 5")
    for row in cursor.fetchall():
        print(row)
        
    conn.close()

if __name__ == "__main__":
    verify()
