import sys
import json
sys.path.insert(0, '/app')
from database_migration import VideoDatabase

db = VideoDatabase()

# Load JSON ratings
with open('/app/ratings.json') as f:
    json_ratings = json.load(f)

# Check how many JSON filenames exist in videos table
with db.get_connection() as conn:
    matched = 0
    for fname in json_ratings.keys():
        exists = conn.execute('SELECT 1 FROM videos WHERE filename = ?', (fname,)).fetchone()
        if exists:
            matched += 1
    
    print(f'JSON ratings filenames that exist in videos: {matched}/{len(json_ratings)}')
    
    # Show first 5 that exist
    print('\nFirst 5 matches:')
    for fname in list(json_ratings.keys())[:10]:
        exists = conn.execute('SELECT 1 FROM videos WHERE filename = ?', (fname,)).fetchone()
        status = 'YES' if exists else 'NO'
        print(f'  {fname[:50]}: {status}')
