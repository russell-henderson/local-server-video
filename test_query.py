import sys
sys.path.insert(0, '/app')
from database_migration import VideoDatabase

db = VideoDatabase()
with db.get_connection() as conn:
    query = '''
        SELECT 
            v.filename,
            COALESCE(r.rating, 0) as rating,
            COALESCE(view.view_count, 0) as views
        FROM videos v
        LEFT JOIN ratings r ON v.filename = r.filename
        LEFT JOIN views view ON v.filename = view.filename
        GROUP BY v.filename, r.rating, view.view_count
        ORDER BY v.added_date DESC
        LIMIT 5
    '''
    rows = conn.execute(query).fetchall()
    print('Test results:')
    for i, row in enumerate(rows):
        d = dict(row)
        print(f'{i+1}. {d["filename"][:40]}: rating={d["rating"]}, views={d["views"]}')
