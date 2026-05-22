import sqlite3
import re
import sys
from pathlib import Path

def auto_tag():
    db_path = Path('data/video_metadata.db')
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        sys.exit(1)

    # Configuration: Known Studio Labels
    KNOWN_STUDIOS = {
        'missax', 'blacked', 'tushy', 'vixen', 'brazzers', 'realitykings', 
        'bangbros', 'digitalplayground', 'evilangel', 'naughtyamerica',
        'deeper', 'milfed', 'pervgw', 'tiny4k', 'trueamateur', 'tushyraw',
        'mommysgirl', 'pure-taboo', 'puretaboo'
    }
    
    # Noise words that commonly appear capitalized in titles but aren't names
    NAME_STOP_WORDS = {
        'horny', 'step', 'mom', 'son', 'begs', 'creampie', 'pussy', 'milf', 
        'just', 'rip', 'it', 'off', 'teaches', 'fuck', 'longer', 'daughter', 
        'pure', 'taboo', 'sons', 'addiction', 'uses', 'revenge', 'watching', 
        'porn', 'with', 'home', 'welcome', 'always', 'good', 'boy', 'give', 
        'thanks', 'part', 'edit', 'girl', 'daddys', 'stepmom', 'stepdaughter',
        'stepson', 'stepdad', 'family', 'taboo', 'forbidden', 'stuck', 'help',
        'needs', 'all', 'around', 'house', 'room', 'bed', 'morning', 'night',
        'day', 'best', 'big', 'huge', 'small', 'tiny', 'thick', 'thin', 'white',
        'black', 'asian', 'latina', 'ebony', 'teen', 'mature', 'older', 'younger'
    }
    
    extensions = {'.mp4', '.webm', '.mkv', '.json', '.avi', '.mov'}
    conjunctions = [r'\s+and\s+', r'\s+&\s+', r'\s+featuring\s+', r'\s+feat\s+', r'\s+vs\s+']
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Fetch filenames
        cursor.execute("SELECT filename FROM videos")
        rows = cursor.fetchall()
        
        tag_data = []
        extracted_studios = set()
        extracted_performers = set()
        analyzed_files = 0

        for row in rows:
            filename = row['filename']
            analyzed_files += 1
            
            # 1. Strip extensions
            stem = filename
            for ext in extensions:
                if stem.lower().endswith(ext):
                    stem = stem[:-len(ext)]
                    break
            
            # 2. Extract Studio (look for known labels)
            # Normalize symbols to spaces for tokenization
            clean_for_studios = re.sub(r'[^a-zA-Z0-9]', ' ', stem)
            tokens = clean_for_studios.split()
            
            for token in tokens:
                low_token = token.lower()
                if low_token in KNOWN_STUDIOS:
                    tag_data.append((filename, low_token))
                    extracted_studios.add(low_token)
            
            # 3. Extract Performer Names (adjacent capitalized words)
            work_stem = stem
            for conj in conjunctions:
                work_stem = re.sub(conj, ' | ', work_stem, flags=re.IGNORECASE)
            
            # Treat common separators as split points
            work_stem = re.sub(r'[-_,\(\)\[\]]', ' | ', work_stem)
            
            # Split into chunks
            chunks = work_stem.split('|')
            
            for chunk in chunks:
                chunk = chunk.strip()
                if not chunk: continue
                
                # Find pairs of Capitalized Words
                # Matches patterns like "Reagan Foxx"
                matches = re.findall(r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b', chunk)
                for first, last in matches:
                    low_first = first.lower()
                    low_last = last.lower()
                    
                    # Filter out noise
                    if low_first in NAME_STOP_WORDS or low_last in NAME_STOP_WORDS:
                        continue
                    
                    # Also skip if it matches a known studio
                    if low_first in KNOWN_STUDIOS or low_last in KNOWN_STUDIOS:
                        continue
                        
                    performer_tag = f"{low_first}-{low_last}"
                    tag_data.append((filename, performer_tag))
                    extracted_performers.add(performer_tag)

        # Step B: Tag Normalization & SQLite Transaction Batching
        if tag_data:
            unique_tag_data = list(set(tag_data))
            
            cursor.executemany(
                "INSERT OR IGNORE INTO video_tags (filename, tag) VALUES (?, ?)",
                unique_tag_data
            )
            conn.commit()
            records_written = cursor.rowcount
        else:
            records_written = 0

        # Step C: Terminal Reporting
        print("=== Advanced Entity Extraction Summary ===")
        print(f"Total unique files analyzed: {analyzed_files}")
        print(f"Total unique studio tags extracted: {len(extracted_studios)}")
        print(f"Total unique performer tags extracted: {len(extracted_performers)}")
        print(f"Total new records successfully written to database: {records_written}")
        print("===========================================")

    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    auto_tag()
