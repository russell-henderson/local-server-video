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
from backend.app.api.schemas import RatingInput
from backend.app.core.rate_limiter import get_rate_limiter


ratings_bp = Blueprint('ratings', __name__, url_prefix='/api/ratings')

# Initialize service
_database = VideoDatabase()
ratings_service = RatingsService(cache, _database)
rate_limiter = get_rate_limiter(max_requests=10, window_seconds=60)


def get_client_ip() -> str:
    """Extract client IP from request, handling proxies."""
    # Check X-Forwarded-For header first (for proxies)
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or '127.0.0.1'


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
        return jsonify({
            "error": "Failed to get rating",
            "detail": str(e)
        }), 500


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
    
    Rate Limit: 10 requests per 60 seconds per IP
    Returns 429 if rate limit exceeded
    """
    # Check rate limit
    client_ip = get_client_ip()
    is_allowed, rate_info = rate_limiter.is_allowed(client_ip)

    if not is_allowed:
        response = jsonify({
            "error": "Rate limit exceeded",
            "detail": f"Max 10 requests per 60 seconds. "
                      f"Reset in {rate_info['reset_in']}s"
        })
        response.status_code = 429
        response.headers['Retry-After'] = str(rate_info['reset_in'])
        return response

    data = request.get_json() or {}
    value = data.get('value')

    # Validate input with Pydantic
    try:
        # Pydantic will handle type coercion and validation
        rating_input = RatingInput(value=value)  # type: ignore
        rating_value = rating_input.value
    except ValueError as e:
        # Pydantic validation error
        return jsonify({
            "error": "Invalid rating value",
            "detail": str(e)
        }), 400
    except Exception as e:
        # Handle other validation errors
        return jsonify({
            "error": "Validation failed",
            "detail": str(e)
        }), 400

    try:
        summary = ratings_service.set_rating(media_hash, rating_value)
        return jsonify(summary), 201
    except ValueError as e:
        return jsonify({
            "error": str(e)
        }), 400
    except FileNotFoundError as e:
        return jsonify({
            "error": str(e)
        }), 404
    except Exception as e:
        return jsonify({
            "error": "Failed to set rating",
            "detail": str(e)
        }), 500


def register_ratings_api(app):
    """Register ratings API blueprint with Flask app."""
    app.register_blueprint(ratings_bp)
