"""
main.py – Local Video Server  (thumbnail pipeline refactor)
"""

import re
import time
import mimetypes
import random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from flask import (
    Flask, Response, request, render_template, send_file,
    abort, url_for, redirect, jsonify
)

from cache_manager import cache
from thumbnail_manager import (
    generate_async as generate_thumbnail_async,
    sync as sync_thumbnails,
)

app = Flask(__name__)


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
    print("✅ Performance monitoring enabled")
except ImportError:
    print("⚠️  Performance monitoring not available")

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
    """Home page – list videos with on-demand thumbnail generation."""
    sort_param = request.args.get("sort", "date")
    order = request.args.get("order", "desc")
    reverse = order == "desc"

    # Metadata via cache_manager
    video_data = cache.get_all_video_data(sort_param, reverse)
    favorites_list = cache.get_favorites()

    # Background thumbnail jobs
    ensure_thumbnails_exist([v["filename"] for v in video_data])

    return render_template(
        "index.html",
        videos=video_data,
        current_sort=sort_param,
        current_order=order,
        favorites_list=favorites_list,
    )


@app.route("/watch/<path:filename>")
@performance_monitor("route_watch")
def watch_video(filename: str):
    """Watch page – serves a single video and related suggestions."""
    file_path = get_video_path(filename)
    if not file_path.exists():
        abort(404)

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

    return render_template(
        "watch.html",
        filename=filename,
        ratings=ratings,
        views=views,
        tags=current_tags,
        videos=paginated,
        page=page,
        total_pages=total,
        favorites_list=favorites_list,
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
    return render_template('tags.html', tags=sorted_tags)


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


@app.route('/admin/performance')
def performance_stats():
    """Performance monitoring endpoint"""
    try:
        from performance_monitor import performance_report
        return f"<pre>{performance_report()}</pre>"
    except ImportError:
        return "Performance monitoring not available"


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

        return jsonify({
            'backend': 'Database (SQLite)' if cache.use_database else 'JSON Files',
            'video_count': len(video_list),
            'favorites_count': len(favorites),
            'cache_ttl': cache.cache_ttl,
            'video_list_ttl': cache.video_list_ttl,
            'cache_ages': cache_ages,
            'recent_videos': video_list[:10] if video_list else []
        })
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
# Advanced Search Endpoints
# ────────────────────────────────────────────────────────────────────────────

@app.route('/search')
def search_page():
    """Advanced search page"""
    try:
        # Get all videos for statistics
        videos = cache.get("all_videos", force_refresh=False) or []
        total_videos = len(videos)
        
        # Get available tags for filtering
        all_tags = set()
        for video in videos:
            video_tags = cache.get(f"tags_{video['filename']}", [])
            all_tags.update(video_tags)
        
        # Sort tags by popularity (most used first)
        available_tags = sorted(all_tags)[:50]  # Limit to top 50 tags
        
        return render_template('search.html', 
                             total_videos=total_videos,
                             available_tags=available_tags)
                             
    except Exception as e:
        print(f"❌ Error loading search page: {e}")
        return render_template('search.html', 
                             total_videos=0,
                             available_tags=[])

@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for performing searches"""
    try:
        from search_engine import get_search_engine, SearchQuery
        
        # Get search parameters
        data = request.get_json() or {}
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'results': [], 'stats': {}})
        
        # Build search query object
        search_query = SearchQuery(
            query=query,
            tags=data.get('tags', []),
            min_duration=data.get('min_duration'),
            max_duration=data.get('max_duration'),
            min_rating=data.get('min_rating'),
            date_from=data.get('date_from'),
            date_to=data.get('date_to'),
            sort_by=data.get('sort_by', 'relevance'),
            sort_order=data.get('sort_order', 'desc'),
            limit=data.get('limit', 50),
            include_fuzzy=data.get('include_fuzzy', True)
        )
        
        # Get search engine and perform search
        search_engine = get_search_engine()
        results = search_engine.search(search_query)
        
        # Convert results to JSON-serializable format
        json_results = []
        for result in results:
            json_results.append({
                'video_path': result.video_path,
                'filename': result.filename,
                'title': result.title,
                'tags': result.tags,
                'relevance_score': result.relevance_score,
                'match_type': result.match_type,
                'duration': result.duration,
                'size': result.size,
                'view_count': result.view_count,
                'rating': result.rating,
                'last_watched': result.last_watched
            })
        
        # Get search statistics
        stats = search_engine.get_search_stats()
        
        return jsonify({
            'results': json_results,
            'stats': stats,
            'query': query,
            'total_results': len(json_results)
        })
        
    except Exception as e:
        print(f"❌ Search API error: {e}")
        return jsonify({
            'error': str(e),
            'results': [],
            'stats': {}
        }), 500

@app.route('/api/search/suggestions')
def api_search_suggestions():
    """API endpoint for search suggestions"""
    try:
        from search_engine import get_search_engine
        
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 10))
        
        if not query or len(query) < 2:
            return jsonify([])
        
        search_engine = get_search_engine()
        suggestions = search_engine.get_search_suggestions(query, limit)
        
        return jsonify(suggestions)
        
    except Exception as e:
        print(f"❌ Suggestions API error: {e}")
        return jsonify([])

@app.route('/api/search/popular')
def api_popular_searches():
    """API endpoint for popular searches"""
    try:
        from search_engine import get_search_engine
        
        limit = int(request.args.get('limit', 10))
        
        search_engine = get_search_engine()
        popular = search_engine.get_popular_searches(limit)
        
        return jsonify(popular)
        
    except Exception as e:
        print(f"❌ Popular searches API error: {e}")
        return jsonify([])

@app.route('/api/search/reindex', methods=['POST'])
def api_reindex_search():
    """API endpoint to reindex search database"""
    try:
        from search_engine import get_search_engine
        
        # Get all video metadata
        videos = cache.get("all_videos", force_refresh=True) or []
        video_metadata = {}
        
        for video in videos:
            filename = video['filename']
            video_path = str(VIDEO_DIR / filename)
            
            # Gather metadata
            metadata = {
                'title': video.get('title', filename),
                'tags': cache.get(f"tags_{filename}", []),
                'duration': video.get('duration', 0),
                'file_size': video.get('size', 0),
                'view_count': cache.get(f"views_{filename}", 0),
                'rating': cache.get(f"rating_{filename}", 0.0),
                'performer_names': []  # Extract from tags if needed
            }
            
            # Extract performer names from tags
            for tag in metadata['tags']:
                if any(name_indicator in tag.lower() for name_indicator in ['performer', 'star', 'actor']):
                    metadata['performer_names'].append(tag)
            
            video_metadata[video_path] = metadata
        
        # Reindex
        search_engine = get_search_engine()
        indexed_count = search_engine.reindex_all_videos(video_metadata)
        
        return jsonify({
            'success': True,
            'indexed_count': indexed_count,
            'total_videos': len(videos)
        })
        
    except Exception as e:
        print(f"❌ Reindex API error: {e}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500


# Import subtitle integration to register routes
try:
    import app_subs_integration
    app_subs_integration.register_subtitle_routes(app)
    print("✅ Subtitle system loaded")
except ImportError as e:
    print(f"⚠️  Subtitle system not available: {e}")


if __name__ == '__main__':
    print("🎬 Starting Video Server with Performance Optimizations...")
    print(f"📁 Video directory: {VIDEO_DIR}")
    print(f"🖼️  Thumbnail directory: {THUMBNAIL_DIR}")
    print(f"💾 Backend: {'Database' if cache.use_database else 'JSON files'}")

    # Run startup tasks with app context
    with app.app_context():
        startup_tasks()

    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
