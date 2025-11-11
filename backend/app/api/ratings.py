"""
backend/app/api/ratings.py

REST API for ratings management.
Endpoints:
  GET /api/ratings/{media_hash} - Get rating summary
  POST /api/ratings/{media_hash} - Set user rating
"""
from pathlib import Path
import sys

from flask import Blueprint, request, jsonify

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from cache_manager import cache
from database_migration import VideoDatabase
from backend.services.ratings_service import RatingsService


ratings_bp = Blueprint('ratings', __name__, url_prefix='/api/ratings')

# Initialize service
_database = VideoDatabase()
ratings_service = RatingsService(cache, _database)


@ratings_bp.route('/<path:media_hash>', methods=['GET'])
def get_rating(media_hash: str):
    """
    Get rating summary for a video.
    
    GET /api/ratings/abc123def456
    
    Returns:
    {
      "average": 4.5,
      "count": 2,
      "user": { "value": 5 }
    }
    """
    try:
        summary = ratings_service.get_rating_summary(media_hash)
        return jsonify(summary)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": "Failed to get rating", "detail": str(e)}), \
               500


@ratings_bp.route('/<path:media_hash>', methods=['POST'])
def set_rating(media_hash: str):
    """
    Set rating for a video.
    
    POST /api/ratings/abc123def456
    Body: { "value": 4 }
    
    Returns:
    {
      "average": 4.0,
      "count": 1,
      "user": { "value": 4 }
    }
    """
    data = request.get_json() or {}
    value = data.get('value')
    
    # Validate input
    is_valid, error_msg = ratings_service.validate_rating(value)
    if not is_valid:
        return jsonify({"error": error_msg}), 400
    
    try:
        # value is guaranteed to be int after validation
        rating_value: int = int(value) if value is not None else 0
        summary = ratings_service.set_rating(media_hash, rating_value)
        return jsonify(summary), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({
            "error": "Failed to set rating",
            "detail": str(e)
        }), 500


def register_ratings_api(app):
    """Register ratings API blueprint with Flask app."""
    app.register_blueprint(ratings_bp)
