import os
import re

VIDEO_DIR = "videos"
THUMBNAIL_DIR = os.path.join("static", "thumbnails")
TERMINAL_LOG = "terminal.log"  # Path to your saved terminal output

def get_video_filenames():
    return set(os.listdir(VIDEO_DIR))

def get_thumbnail_filenames():
    return set(os.listdir(THUMBNAIL_DIR))

def parse_terminal_log(log_path):
    """Parse terminal log for thumbnail 404s and 304s."""
    not_found = []
    found = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            # Example: GET /static/thumbnails/filename.jpg HTTP/1.1" 404 -
            m = re.search(r'GET /static/thumbnails/(.+?\.jpg) HTTP/1\.1"\s+(\d+)', line)
            if m:
                thumb, code = m.group(1), m.group(2)
                if code == "404":
                    not_found.append(thumb)
                elif code == "304":
                    found.append(thumb)
    return not_found, found

def analyze_thumbnails():
    video_files = get_video_filenames()
    thumb_files = get_thumbnail_filenames()
    not_found, found = parse_terminal_log(TERMINAL_LOG)

    print("--- Analysis Report ---")
    print(f"Total videos: {len(video_files)}")
    print(f"Total thumbnails: {len(thumb_files)}")
    print(f"404 thumbnails in log: {len(not_found)}")
    print(f"304 thumbnails in log: {len(found)}")

    # Check if 404 thumbnails correspond to any video
    for thumb in not_found:
        base = os.path.splitext(thumb)[0] + ".mp4"
        if base not in video_files:
            print(f"404: {thumb} (no matching video)")
        else:
            print(f"404: {thumb} (video exists, thumbnail missing)")

    # Check for thumbnails that exist but shouldn't
    for thumb in thumb_files:
        base = os.path.splitext(thumb)[0] + ".mp4"
        if base not in video_files:
            print(f"Orphan thumbnail: {thumb} (no matching video)")

    print("--- End of Report ---")

if __name__ == "__main__":
    analyze_thumbnails()
