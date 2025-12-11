"""
main.py – Local Video Server  (thumbnail pipeline refactor)
"""

import re
import time
import mimetypes
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from flask import (
    Flask, Response, request, render_template, send_file,
    abort, url_for, redirect, jsonify, g
)

from cache_manager import cache
from thumbnail_manager import (
    generate_async as generate_thumbnail_async,
    sync as sync_thumbnails,
)
from config import get_config
import json

# Register API blueprints
try:
    from backend.app.api.ratings import register_ratings_api
    _ratings_api_available = True
except ImportError:
    _ratings_api_available = False

try:
    from backend.app.admin.routes import register_admin_routes
    _admin_routes_available = True
except ImportError:
    _admin_routes_available = False

app = Flask(__name__)

# Register ratings API if available
if _ratings_api_available:
    register_ratings_api(app)

# Register admin routes if available
if _admin_routes_available:
    register_admin_routes(app)


# ────────────────────────────────────────────────────────────────────────────
# Simple connectivity test endpoint
# ────────────────────────────────────────────────────────────────────────────

@app.route("/ping")
def ping():
    """Basic health-check used by uptime monitors."""
    return jsonify({"status": "ok", "message": "Server is reachable"})


@app.route('/favicon.ico')
def favicon():
    """Avoid 404s for favicon requests."""
    return ("", 204)


# ────────────────────────────────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────────────────────────────────


VIDEO_DIR = Path("videos")
THUMBNAIL_DIR = Path("static") / "thumbnails"
INDEX_DEFAULT_PER_PAGE = 60
INDEX_MAX_PER_PAGE = 120

# Guarantee required folders exist
THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)

# Thread pool for misc background jobs (already used by thumbnail_manager)
executor = ThreadPoolExecutor(max_workers=2)


# ────────────────────────────────────────────────────────────────────────────
# Optional performance monitoring
# ────────────────────────────────────────────────────────────────────────────

try:
    from performance_monitor import flask_route_monitor, performance_monitor  # type: ignore
    app = flask_route_monitor(app)
    print("[OK] Performance monitoring enabled")
except ImportError:
    print("[WARN] Performance monitoring not available")

    def performance_monitor(arg=None):
        # Support both @performance_monitor and @performance_monitor("name")
        def decorator(fn):
            return fn
        if callable(arg):
            # Used as @performance_monitor without parentheses
            return decorator(arg)
        else:
            # Used as @performance_monitor("name") or @performance_monitor()
            return decorator


# ────────────────────────────────────────────────────────────────────────────
# Request timing logs (lightweight)
# ────────────────────────────────────────────────────────────────────────────

def _is_perf_log_enabled() -> bool:
    """Return whether perf logging should run."""
    cfg = get_config()
    return getattr(cfg, "enable_perf_log", True)


@app.before_request
def _perf_log_before_request():
    enabled = _is_perf_log_enabled()
    g._perf_log_enabled = enabled
    if not enabled:
        return
    g._perf_log_start = time.perf_counter()


@app.after_request
def _perf_log_after_request(response):
    if not getattr(g, "_perf_log_enabled", False):
        return response
    start = getattr(g, "_perf_log_start", None)
    if start is None:
        return response

    duration_ms = (time.perf_counter() - start) * 1000
    ts = datetime.utcnow().isoformat()
    app.logger.info(
        "[PERF] ts=%s method=%s path=%s status=%s duration_ms=%.2f",
        ts,
        request.method,
        request.path,
        response.status_code,
        duration_ms,
    )
    return response


# ────────────────────────────────────────────────────────────────────────────
# Utility helpers
# ────────────────────────────────────────────────────────────────────────────

def get_video_path(filename: str) -> Path:
    """Return the absolute Path to a video inside VIDEO_DIR."""
    return VIDEO_DIR / filename


def ensure_thumbnails_exist(video_list: list[str]) -> None:
    """
    Queue thumbnail generation for every file in `video_list`.
    `thumbnail_manager` handles duplication and existence checks.
    """
    for vid in video_list:
        generate_thumbnail_async(vid)


# ────────────────────────────────────────────────────────────────────────────
# Optimised routes
# ────────────────────────────────────────────────────────────────────────────

@app.route("/")
@performance_monitor("route_index")
def index():
    """Home page - list videos with on-demand thumbnail generation."""
    sort_param = request.args.get("sort", "date")
    order = request.args.get("order", "desc")
    reverse = order == "desc"
    try:
        page = int(request.args.get("page", "1"))
    except (TypeError, ValueError):
        page = 1
    try:
        per_page = int(request.args.get("per_page", str(INDEX_DEFAULT_PER_PAGE)))
    except (TypeError, ValueError):
        per_page = INDEX_DEFAULT_PER_PAGE

    page = max(1, page)
    per_page = max(1, min(per_page, INDEX_MAX_PER_PAGE))
    offset = (page - 1) * per_page

    total_videos = len(cache.get_video_list())
    if offset >= total_videos and total_videos:
        page = max(1, (total_videos - 1) // per_page + 1)
        offset = (page - 1) * per_page

    # Metadata via cache_manager
    video_data = cache.get_all_video_data(sort_param, reverse, limit=per_page, offset=offset)
    total_pages = max(1, (total_videos + per_page - 1) // per_page)
    favorites_list = cache.get_favorites()

    # Background thumbnail jobs
    ensure_thumbnails_exist([v["filename"] for v in video_data])

    # Load config for feature flags
    config = get_config()

    return render_template(
        "index.html",
        videos=video_data,
        current_sort=sort_param,
        current_order=order,
        current_page=page,
        total_pages=total_pages,
        per_page=per_page,
        total_videos=total_videos,
        favorites_list=favorites_list,
        feature_vr_simplify=config.feature_vr_simplify,
        feature_previews=config.feature_previews,
    )


@app.route("/watch/<path:filename>")
@performance_monitor("route_watch")
def watch_video(filename: str):
    """Watch page – serves a single video and related suggestions."""
    file_path = get_video_path(filename)
    if not file_path.exists():
        abort(404)

    # Compute media_hash (use RatingsService utility if available)
    try:
        from backend.services.ratings_service import RatingsService
        media_hash = RatingsService.get_media_hash(filename)
    except (ImportError, Exception):
        # Fallback: use filename as hash
        media_hash = filename

    # Pull all cached metadata in bulk
    ratings = cache.get_ratings()
    views = cache.get_views()
    all_tags = cache.get_tags()
    favorites_list = cache.get_favorites()

    current_tags = all_tags.get(filename, [])
    related_videos = cache.get_related_videos_optimized(filename, 20)

    # Pagination
    page = int(request.args.get("page", 1))
    per_page = 12
    start, end = (page - 1) * per_page, (page - 1) * per_page + per_page
    paginated = related_videos[start:end]
    total = (len(related_videos) + per_page - 1) // per_page

    # Thumbnails for related videos
    ensure_thumbnails_exist([v["filename"] for v in paginated])

    # Load config for feature flags
    config = get_config()

    return render_template(
        "watch.html",
        filename=filename,
        media_hash=media_hash,
        ratings=ratings,
        views=views,
        tags=current_tags,
        videos=paginated,
        page=page,
        total_pages=total,
        favorites_list=favorites_list,
        feature_vr_simplify=config.feature_vr_simplify,
        feature_previews=config.feature_previews,
    )


@app.route("/video/<path:filename>")
def stream_video(filename: str):
    """Byte-range streaming endpoint with basic Range support."""
    file_path = get_video_path(filename)
    if not file_path.exists():
        abort(404)

    mime_type, _ = mimetypes.guess_type(str(file_path))
    mime_type = mime_type or "application/octet-stream"
    range_hdr = request.headers.get("Range")

    if not range_hdr:
        # No range – send whole file
        return send_file(str(file_path), mimetype=mime_type)

    size = file_path.stat().st_size
    byte1, byte2 = 0, None
    m = re.search(r"bytes=(\d+)-(\d*)", range_hdr)
    if m:
        g1, g2 = m.groups()
        if g1:
            byte1 = int(g1)
        if g2:
            byte2 = int(g2)

    if byte2 is None or byte2 >= size:
        byte2 = size - 1
    length = byte2 - byte1 + 1

    with file_path.open("rb") as fh:
        fh.seek(byte1)
        data = fh.read(length)

    rv = Response(data, 206, mimetype=mime_type, direct_passthrough=True)
    rv.headers.add("Content-Range", f"bytes {byte1}-{byte2}/{size}")
    rv.headers.add("Accept-Ranges", "bytes")
    rv.headers.add("Content-Length", str(length))
    return rv


@app.route("/get_views")
@performance_monitor("route_get_views")
def get_views_route():
    """Optimized views endpoint using cache"""
    try:
        views = cache.get_views()
        return jsonify(views)
    except OSError as e:
        print(f"Error loading views: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/rate', methods=['POST'])
@performance_monitor("route_rate")
def rate_video():
    """Optimized rating with write-through cache"""
    data = request.get_json()
    filename = data.get('filename')
    rating = data.get('rating')

    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            return {"error": "Invalid rating"}, 400
    except (ValueError, TypeError):
        return {"error": "Invalid rating"}, 400

    # Update through cache
    cache.update_rating(filename, rating)

    return {"success": True, "rating": rating}


@app.route('/view', methods=['POST'])
@performance_monitor("route_view")
def record_view():
    """Optimized view recording with write-through cache"""
    data = request.get_json()
    filename = data.get('filename')

    # Update through cache
    new_view_count = cache.update_view(filename)

    return {"success": True, "views": new_view_count}


@app.route('/tag', methods=['POST'])
@performance_monitor("route_add_tag")
def add_tag():
    """Optimized tag addition with write-through cache"""
    data = request.get_json()
    filename = data.get('filename')
    tag = data.get('tag', '').strip()

    if not tag:
        return {"error": "No tag provided"}, 400

    if not tag.startswith("#"):
        tag = "#" + tag

    # Get current tags from cache
    all_tags = cache.get_tags()
    current_tags = all_tags.get(filename, [])

    # Check for duplicates case-insensitively
    if tag.lower() not in [t.lower() for t in current_tags]:
        current_tags.append(tag)
        cache.update_tags(filename, current_tags)

    return {"success": True, "tags": current_tags}


@app.route('/delete_tag', methods=['POST'])
@performance_monitor("route_delete_tag")
def delete_tag():
    """Optimized tag deletion with write-through cache"""
    data = request.get_json()
    filename = data.get('filename')
    tag = data.get('tag', '').strip()

    if not tag:
        return {"error": "No tag provided"}, 400

    # Get current tags from cache
    all_tags = cache.get_tags()
    current_tags = all_tags.get(filename, [])

    if current_tags:
        updated_tags = [t for t in current_tags if t.lower() != tag.lower()]
        cache.update_tags(filename, updated_tags)
        return {"success": True, "tags": updated_tags}

    return {"error": "Video not found in tags"}, 404


@app.route('/api/tags/popular')
def popular_tags_api():
    """Expose most-used tags for autocomplete."""
    limit = request.args.get('limit', default=50, type=int)
    limit = max(1, min(limit or 50, 200))
    tags = cache.get_popular_tags(limit)
    return jsonify({"tags": tags})


@app.route("/favorite", methods=["POST"])
@performance_monitor("route_toggle_favorite")
def toggle_favorite():
    """Optimized favorite toggle with write-through cache"""
    data = request.get_json()
    filename = data.get("filename")

    favorites = cache.get_favorites()

    if filename in favorites:
        favorites.remove(filename)
    else:
        favorites.append(filename)

    cache.update_favorites(favorites)

    return jsonify({"success": True, "favorites": favorites})


@app.route("/favorites")
@performance_monitor("route_favorites")
def favorites_page():
    """Optimized favorites page with cached data"""
    favorites = cache.get_favorites()

    # Get metadata for favorite videos efficiently
    if cache.use_database and cache.db:
        # Database can do this efficiently
        video_data = []
        for video in favorites:
            metadata = cache.db.get_video_by_filename(video)
            if metadata:  # Only include if video still exists
                video_data.append(metadata)
    else:
        # Use cache for JSON fallback
        video_data = []
        all_video_data = cache.get_all_video_data()
        favorite_set = set(favorites)
        for video in all_video_data:
            if video['filename'] in favorite_set:
                video_data.append(video)

    # Ensure thumbnails exist
    ensure_thumbnails_exist([v['filename'] for v in video_data])

    return render_template("favorites.html", videos=video_data)


@app.route('/random')
@performance_monitor("route_random")
def random_video():
    """Optimized random video selection using cached list"""
    videos = cache.get_video_list()
    if videos:
        selected_video = random.choice(videos)
        return redirect(url_for('watch_video', filename=selected_video))
    return redirect(url_for('index'))


@app.route('/tags')
@performance_monitor("route_tags")
def tags_page():
    """Optimized tags page with cached data"""
    sorted_tags = cache.get_all_unique_tags()
    return render_template('tags.html', tags=sorted_tags, tag_count=len(sorted_tags))


@app.route('/tag/<tag>')
@performance_monitor("route_tag_videos")
def tag_videos(tag):
    """Optimized tag filtering with cached data"""
    normalized_tag = tag.lstrip("#")

    # Use optimized tag filtering
    filtered_videos = cache.get_videos_by_tag_optimized(normalized_tag)

    # Ensure thumbnails exist
    ensure_thumbnails_exist([v['filename'] for v in filtered_videos])

    return render_template('tag_videos.html', tag=normalized_tag, videos=filtered_videos)


@app.route('/best-of')
@performance_monitor("route_best_of")
def best_of():
    """Best of page - videos with 4+ star ratings"""
    # Get all data in one call to reduce cache hits
    if cache.use_database and cache.db:
        # Database can filter efficiently
        all_video_data = cache.get_all_video_data()
        video_data = [video for video in all_video_data if video.get('rating', 0) >= 4]
        favorites_list = cache.get_favorites()
    else:
        # JSON fallback - get all data at once
        ratings = cache.get_ratings()
        favorites_list = cache.get_favorites()
        all_video_data = cache.get_all_video_data()
        
        # Filter and enrich in memory
        high_rated_set = {filename for filename, rating in ratings.items() if rating >= 4}
        video_data = [video for video in all_video_data if video['filename'] in high_rated_set]
    
    # Sort by rating (highest first)
    video_data.sort(key=lambda x: x.get('rating', 0), reverse=True)
    
    # Ensure thumbnails exist
    ensure_thumbnails_exist([v['filename'] for v in video_data])
    
    return render_template('best_of.html', videos=video_data, favorites_list=favorites_list)


@app.route('/links')
def links():
    """Links page"""
    return render_template('links.html')


@app.route('/gallery')
def gallery():
    """Gallery page for images"""
    from database_migration import VideoDatabase
    
    gallery_dir = Path('images/gallery')
    images = []
    if gallery_dir.exists():
        # Get all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        images = [
            img.name for img in gallery_dir.iterdir()
            if img.is_file() and img.suffix.lower() in image_extensions
        ]
    
    print(f"\n=== GALLERY DEBUG ===")
    print(f"All files in gallery: {images}")
    
    # Exclude images that are already in groups
    try:
        db = VideoDatabase()
        grouped_images = set()
        all_groups = db.get_gallery_groups()
        print(f"Total groups: {len(all_groups)}")
        for group in all_groups:
            group_items = db.get_group_images(group['id'])
            print(f"Group '{group['name']}' (ID {group['id']}) items: {group_items}")
            grouped_images.update(group_items)
        
        print(f"All grouped images: {grouped_images}")
        print(f"Gallery before filter: {len(images)} images")
        images = [img for img in images if img not in grouped_images]
        print(f"Gallery after filter: {len(images)} images")
        print(f"Filtered images: {images}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    images.sort(reverse=True)  # Newest first
    print(f"=== END DEBUG ===\n")
    return render_template('gallery.html', images=images)


@app.route('/gallery/image/<path:filename>')
def serve_gallery_image(filename: str):
    """Serve gallery images"""
    # Prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        abort(403)
    
    file_path = Path('images/gallery') / filename
    if not file_path.exists() or not file_path.is_file():
        abort(404)
    
    mime_type, _ = mimetypes.guess_type(str(file_path))
    mime_type = mime_type or "application/octet-stream"
    return send_file(str(file_path), mimetype=mime_type)


@app.route('/gallery/groups/<slug>')
def gallery_group(slug: str):
    """Display a specific gallery group"""
    from database_migration import VideoDatabase
    db = VideoDatabase()
    
    # Get group info
    group_data = db.get_gallery_group_by_slug(slug)
    if not group_data:
        abort(404)
    
    # Type narrowing: group_data is dict[str, Any] after the None check
    assert isinstance(group_data, dict), "group_data must be a dict"
    group_id: int = group_data.get('id', 0)
    images = db.get_group_images_with_ids(group_id)
    
    return render_template(
        'gallery_group.html',
        group=group_data,
        images=images
    )


# ─── Gallery API Endpoints ──────────────────────────────────────────

@app.route('/api/gallery', methods=['GET'])
def api_gallery_images():
    """Get list of all gallery images"""
    gallery_dir = Path('images/gallery')
    if not gallery_dir.exists():
        return jsonify({'images': []})
    
    images = []
    try:
        for item in gallery_dir.iterdir():
            if item.is_file() and item.suffix.lower() in [
                '.jpg', '.jpeg', '.png', '.gif', '.webp'
            ]:
                images.append(item.name)
    except Exception:
        pass
    
    return jsonify({'images': sorted(images)})


@app.route('/api/gallery/groups', methods=['GET', 'POST'])
def api_gallery_groups():
    """Get all gallery groups or create a new one"""
    from database_migration import VideoDatabase
    db = VideoDatabase()
    
    if request.method == 'GET':
        groups = db.get_gallery_groups()
        return jsonify(groups)
    
    # POST: Create new group
    data = request.get_json()
    name = data.get('name', '').strip()
    images = data.get('images', [])
    cover_image = data.get('cover_image')
    
    if not name or not images:
        return jsonify({'error': 'Name and images required'}), 400
    
    try:
        group_id = db.create_gallery_group(name, cover_image)
        db.add_images_to_group(group_id, images)
        
        # Get the created group
        group = db.get_gallery_group_by_slug(
            name.lower().replace(' ', '-')
        )
        return jsonify(group), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/gallery/groups/<int:group_id>/images',
           methods=['POST'])
def api_add_images_to_group(group_id: int):
    """Add images to an existing group"""
    from database_migration import VideoDatabase
    db = VideoDatabase()
    
    data = request.get_json()
    images = data.get('images', [])
    
    if not images:
        return jsonify({'error': 'Images required'}), 400
    
    try:
        db.add_images_to_group(group_id, images)
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/gallery/groups/<int:group_id>/images/<path:image_path>',
           methods=['DELETE'])
def api_remove_image_from_group(group_id: int, image_path: str):
    """Remove an image from a group"""
    from database_migration import VideoDatabase
    db = VideoDatabase()
    
    try:
        db.remove_image_from_group(group_id, image_path)
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/gallery/groups/<int:group_id>/items/<int:item_id>',
           methods=['DELETE'])
def api_remove_image_item(group_id: int, item_id: int):
    """Remove a specific image item from a group by ID"""
    from database_migration import VideoDatabase
    db = VideoDatabase()
    
    try:
        db.remove_image_item_by_id(item_id)
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/gallery/groups/<int:group_id>', methods=['PUT', 'DELETE'])
def api_modify_group(group_id: int):
    """Update or delete a gallery group"""
    from database_migration import VideoDatabase
    db = VideoDatabase()
    
    if request.method == 'PUT':
        # Update group name or cover image
        data = request.get_json()
        name = data.get('name', '').strip()
        cover_image = data.get('cover_image', '').strip()
        
        try:
            if name:
                db.update_group_name(group_id, name)
            if cover_image:
                db.update_group_cover_image(group_id, cover_image)
            return jsonify({'success': True}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            db.delete_gallery_group(group_id)
            return jsonify({'success': True}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# ─── BACKGROUND TASKS & STARTUP ─────────────────────────────────────


def startup_tasks():
    """Run startup tasks in background"""
    def warm_cache():
        """Warm up the cache: clean metadata/DB, remove orphan thumbnails, and queue missing thumbnails"""
        print("🚀 Warming up cache...")
        # Single authoritative sweep (cleans JSON/DB + orphan thumbs, queues missing)
        try:
            sync_thumbnails(force_regen=False)
        except Exception as e:
            print(f"⚠️  Thumbnail sync failed: {e}")
        videos = cache.get_video_list()
        print(f"📹 Found {len(videos)} videos")
        print("✅ Cache warmed and thumbnail maintenance started")
    executor.submit(warm_cache)

# ─── PERFORMANCE MONITORING ENDPOINTS ───────────────────────────────


@app.route('/admin/cache/status')
def cache_status():
    """Cache status endpoint with detailed information"""
    try:
        video_list = cache.get_video_list()
        favorites = cache.get_favorites()

        # Get cache age information
        current_time = time.time()
        cache_ages = {}
        # Use public methods if available, else fallback
        last_refresh = getattr(cache, 'last_refresh', None)
        is_cache_valid = getattr(cache, 'is_cache_valid', None)
        if last_refresh and is_cache_valid:
            for key, last_time in last_refresh.items():
                cache_ages[key] = {
                    'last_refresh': last_time,
                    'age_seconds': current_time - last_time,
                    'is_valid': is_cache_valid(key)
                }
        else:
            # Fallback: skip cache age details if not available
            pass

        preview_cache = {}
        try:
            from performance_monitor import _cache_metrics  # type: ignore
            preview_cache = _cache_metrics()
        except Exception:
            preview_cache = {}

        payload = {
            'backend': 'Database (SQLite)' if cache.use_database else 'JSON Files',
            'video_count': len(video_list),
            'favorites_count': len(favorites),
            'cache_ttl': cache.cache_ttl,
            'video_list_ttl': cache.video_list_ttl,
            'cache_ages': cache_ages,
            'recent_videos': video_list[:10] if video_list else []
        }
        payload.update(preview_cache)
        return jsonify(payload)
    except (OSError, AttributeError) as e:
        return jsonify({"error": str(e)}), 500


@app.route('/admin/cache/refresh', methods=['POST'])
def refresh_cache():
    """Force cache refresh endpoint"""
    try:
        cache.refresh_all()
        return jsonify({"success": True, "message": "Cache refreshed"})
    except OSError as e:
        return jsonify({"error": str(e)}), 500





@app.route('/analytics/save', methods=['POST'])
@performance_monitor("route_analytics_save")
def save_analytics():
    """Save video analytics data"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    try:
        # Save analytics to a JSON file (could be database in future)
        analytics_file = Path("video_analytics.json")
        
        existing_data = {}
        if analytics_file.exists():
            try:
                existing_data = json.loads(analytics_file.read_text(encoding="utf-8"))
            except Exception:
                existing_data = {}
        
        # Merge new data with existing
        video_id = data.get('videoId')
        if video_id:
            existing_data[video_id] = data.get('analytics', {})
            
            # Write back to file
            analytics_file.write_text(json.dumps(existing_data, indent=2), encoding="utf-8")
            
            return jsonify({"success": True, "message": "Analytics saved"})
        else:
            return jsonify({"error": "Video ID required"}), 400
            
    except Exception as e:
        return jsonify({"error": f"Failed to save analytics: {str(e)}"}), 500


@app.route('/analytics/get/<path:filename>')
@performance_monitor("route_analytics_get")
def get_analytics(filename):
    """Get analytics data for a specific video"""
    try:
        analytics_file = Path("video_analytics.json")
        
        if not analytics_file.exists():
            return jsonify({"analytics": None})
        
        analytics_data = json.loads(analytics_file.read_text(encoding="utf-8"))
        video_analytics = analytics_data.get(filename, None)
        
        return jsonify({"analytics": video_analytics})
        
    except Exception as e:
        return jsonify({"error": f"Failed to get analytics: {str(e)}"}), 500


@app.route('/analytics/export')
@performance_monitor("route_analytics_export")
def export_analytics():
    """Export all analytics data"""
    try:
        analytics_file = Path("video_analytics.json")
        
        if not analytics_file.exists():
            return jsonify({"analytics": {}})
        
        analytics_data = json.loads(analytics_file.read_text(encoding="utf-8"))
        
        # Add summary statistics
        summary = {
            "totalVideos": len(analytics_data),
            "exportDate": time.strftime("%Y-%m-%d %H:%M:%S"),
            "analytics": analytics_data
        }
        
        return jsonify(summary)
        
    except Exception as e:
        return jsonify({"error": f"Failed to export analytics: {str(e)}"}), 500


@app.route('/analytics/stats')
@performance_monitor("route_analytics_stats")
def analytics_stats():
    """Get overall analytics statistics"""
    try:
        analytics_file = Path("video_analytics.json")
        
        if not analytics_file.exists():
            return jsonify({"stats": {"totalVideos": 0, "totalWatchTime": 0}})
        
        analytics_data = json.loads(analytics_file.read_text(encoding="utf-8"))
        
        total_videos = len(analytics_data)
        total_watch_time = 0
        total_views = 0
        most_watched = None
        highest_completion = 0
        
        for video_id, data in analytics_data.items():
            total_watch_time += data.get('totalWatchTime', 0)
            total_views += data.get('watchCount', 0)
            
            completion = data.get('completionPercentage', 0)
            if completion > highest_completion:
                highest_completion = completion
                most_watched = video_id
        
        stats = {
            "totalVideos": total_videos,
            "totalWatchTime": round(total_watch_time / 60, 1),  # in minutes
            "totalViews": total_views,
            "mostWatchedVideo": most_watched,
            "highestCompletion": round(highest_completion, 1)
        }
        
        return jsonify({"stats": stats})
        
    except Exception as e:
        return jsonify({"error": f"Failed to get stats: {str(e)}"}), 500

# ─── CLEANUP ─────────────────────────────────────────────────────


@app.teardown_appcontext
def cleanup(_error):
    """Cleanup resources"""
    # No cleanup needed - cache handles persistence automatically
    return None


# ────────────────────────────────────────────────────────────────────────────
# Subtitle system removed — no subtitle routes registered


if __name__ == '__main__':
    print("[STARTUP] Starting Video Server with Performance Optimizations...")
    print(f"[STARTUP] Video directory: {VIDEO_DIR}")
    print(f"[STARTUP] Thumbnail directory: {THUMBNAIL_DIR}")
    backend = 'Database' if cache.use_database else 'JSON files'
    print(f"[STARTUP] Backend: {backend}")

    # Run startup tasks with app context
    with app.app_context():
        startup_tasks()

    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
