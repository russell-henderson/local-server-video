import sys
sys.path.insert(0, '/app')
from database_migration import VideoDatabase

db = VideoDatabase()
with db.get_connection() as conn:
    total_videos = conn.execute('SELECT COUNT(*) FROM videos').fetchone()[0]
    total_ratings = conn.execute('SELECT COUNT(*) FROM ratings').fetchone()[0]
    matching_ratings = conn.execute('''
        SELECT COUNT(*) FROM ratings r
        WHERE EXISTS (SELECT 1 FROM videos v WHERE v.filename = r.filename)
    ''').fetchone()[0]
    
    print(f'Total videos in DB: {total_videos}')
    print(f'Total ratings in DB: {total_ratings}')
    print(f'Matching ratings (video exists): {matching_ratings}')
    print(f'Orphaned ratings (video missing): {total_ratings - matching_ratings}')
    print(f'Match rate: {matching_ratings}/{total_ratings} = {100*matching_ratings/total_ratings:.1f}%')
