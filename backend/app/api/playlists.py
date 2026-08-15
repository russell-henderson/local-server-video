"""Playlists API endpoints."""
from pathlib import Path

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from backend.app.services.playlists_service import PlaylistsService

playlists_bp = Blueprint("playlists", __name__, url_prefix="/api/playlists")
service = PlaylistsService()

COVER_DIR = Path("static") / "playlist_covers"
ALLOWED_COVER_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_COVER_BYTES = 5 * 1024 * 1024


def _cover_files_for_playlist(playlist_id: int):
    if not COVER_DIR.exists():
        return []
    return list(COVER_DIR.glob(f"{playlist_id}.*"))

@playlists_bp.route("", methods=["GET"])
def get_playlists():
    """List all playlists with item counts."""
    playlists = service.get_playlists()
    # Add counts manually for each playlist
    with service.db.get_session() as conn:
        for p in playlists:
            row = conn.execute(
                "SELECT COUNT(*) FROM playlist_items WHERE playlist_id = ?",
                (p['id'],)
            ).fetchone()
            p['item_count'] = row[0]
    return jsonify({"success": True, "playlists": playlists})

@playlists_bp.route("", methods=["POST"])
def create_playlist():
    """Create a new playlist."""
    data = request.get_json() or {}
    name = data.get("name")
    description = data.get("description")
    
    if not name:
        return jsonify({"success": False, "error": "Name is required"}), 400
        
    result = service.create_playlist(name, description)
    return jsonify(result), 201 if result["success"] else 400


@playlists_bp.route("/summary", methods=["GET"])
def playlists_summary():
    """Return lightweight playlist dashboard summary data."""
    return jsonify(service.get_summary())

@playlists_bp.route("/<int:playlist_id>", methods=["GET"])
def get_playlist(playlist_id):
    """Get playlist details and items."""
    result = service.get_playlist_queue(playlist_id)
    return jsonify(result), 200 if result["success"] else 404


@playlists_bp.route("/<int:playlist_id>/metadata", methods=["PATCH"])
def update_playlist_metadata(playlist_id):
    """Update additive playlist metadata fields."""
    result = service.update_metadata(playlist_id, request.get_json() or {})
    if result.get("success"):
        return jsonify(result)
    status = 404 if result.get("error") == "Playlist not found." else 400
    return jsonify(result), status


@playlists_bp.route("/<int:playlist_id>/cover", methods=["POST"])
def upload_playlist_cover(playlist_id):
    """Upload or replace a playlist cover image."""
    if request.content_length and request.content_length > MAX_COVER_BYTES:
        return jsonify({"success": False, "error": "Cover image must be 5 MB or smaller."}), 400

    upload = request.files.get("cover")
    if not upload or not upload.filename:
        return jsonify({"success": False, "error": "Cover file is required."}), 400

    extension = Path(secure_filename(upload.filename)).suffix.lower()
    if extension not in ALLOWED_COVER_EXTENSIONS:
        return jsonify({"success": False, "error": "Cover must be JPG, PNG, or WebP."}), 400

    playlist = service.get_playlist(playlist_id)
    if not playlist.get("success"):
        return jsonify(playlist), 404

    COVER_DIR.mkdir(parents=True, exist_ok=True)
    destination = COVER_DIR / f"{playlist_id}{extension}"
    upload.save(destination)

    for old_cover in _cover_files_for_playlist(playlist_id):
        if old_cover != destination and old_cover.exists():
            old_cover.unlink()

    cover_path = f"/static/playlist_covers/{destination.name}"
    result = service.update_cover(playlist_id, cover_path)
    return jsonify({"success": result.get("success", False), "cover_image": cover_path, "playlist": result})


@playlists_bp.route("/<int:playlist_id>/cover", methods=["DELETE"])
def delete_playlist_cover(playlist_id):
    """Remove a playlist cover image if present."""
    playlist = service.get_playlist(playlist_id)
    if not playlist.get("success"):
        return jsonify(playlist), 404

    for old_cover in _cover_files_for_playlist(playlist_id):
        if old_cover.exists():
            old_cover.unlink()

    result = service.update_cover(playlist_id, None)
    return jsonify({"success": result.get("success", False), "playlist": result})

@playlists_bp.route("/<int:playlist_id>", methods=["DELETE"])
def delete_playlist(playlist_id):
    """Delete a playlist."""
    result = service.delete_playlist(playlist_id)
    return jsonify(result), 200 if result["success"] else 400

@playlists_bp.route("/<int:playlist_id>/add", methods=["POST"])
def add_to_playlist(playlist_id):
    """Add a video to a playlist."""
    data = request.get_json() or {}
    video_filename = data.get("video_filename")
    
    if not video_filename:
        return jsonify({"success": False, "error": "video_filename is required"}), 400
        
    result = service.add_to_playlist(playlist_id, video_filename)
    return jsonify(result), 200 if result["success"] else 400

@playlists_bp.route("/<int:playlist_id>/items/<path:filename>", methods=["DELETE"])
def remove_from_playlist(playlist_id, filename):
    """Remove a video from a playlist."""
    position = request.args.get("position", type=int)
    result = service.remove_from_playlist(playlist_id, filename, position)
    return jsonify(result), 200 if result["success"] else 400

@playlists_bp.route("/<int:playlist_id>/rating", methods=["POST"])
def set_playlist_rating(playlist_id):
    """Set or update the rating for a playlist."""
    data = request.get_json() or {}
    rating = data.get("rating")
    
    if rating is not None:
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "Rating must be an integer between 1 and 5"}), 400
    else:
        return jsonify({"success": False, "error": "Rating is required"}), 400

    result = service.set_playlist_rating(playlist_id, rating)
    return jsonify(result), 200 if result.get("success") else 404

def register_playlists_api(app):
    """Register playlists blueprint with Flask app."""
    app.register_blueprint(playlists_bp)
    return playlists_bp
