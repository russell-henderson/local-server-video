"""Playlists API endpoints."""
from flask import Blueprint, jsonify, request
from backend.app.services.playlists_service import PlaylistsService

playlists_bp = Blueprint("playlists", __name__, url_prefix="/api/playlists")
service = PlaylistsService()

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

@playlists_bp.route("/<int:playlist_id>", methods=["GET"])
def get_playlist(playlist_id):
    """Get playlist details and items."""
    result = service.get_playlist_queue(playlist_id)
    return jsonify(result), 200 if result["success"] else 404

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

def register_playlists_api(app):
    """Register playlists blueprint with Flask app."""
    app.register_blueprint(playlists_bp)
    return playlists_bp
