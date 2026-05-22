import sys
sys.path.insert(0, '/app')
from database_migration import VideoDatabase

db = VideoDatabase()
with db.get_connection() as conn:
    # Get a sample video filename from videos table
    v_row = conn.execute('SELECT filename FROM videos LIMIT 1').fetchone()
    video_filename = dict(v_row)['filename']
    print(f'Sample video filename: {video_filename}')
    
    # Check if this exact filename exists in ratings
    r_row = conn.execute('SELECT rating FROM ratings WHERE filename = ?', (video_filename,)).fetchone()
    if r_row:
        print(f'Found in ratings: {dict(r_row)["rating"]}')
    else:
        print('NOT found in ratings')
    
    # Check what filenames ARE in ratings
    ratings_samples = conn.execute('SELECT filename FROM ratings LIMIT 3').fetchall()
    print(f'\nSample filenames in ratings table:')
    for r in ratings_samples:
        print(f'  {dict(r)["filename"][:50]}')
    
    # Check if they exist in videos
    print('\nDo these filenames exist in videos?')
    for r in ratings_samples:
        fname = dict(r)['filename']
        exists = conn.execute('SELECT COUNT(*) FROM videos WHERE filename = ?', (fname,)).fetchone()[0]
        print(f'  {fname[:40]}: {"YES" if exists else "NO"}')
