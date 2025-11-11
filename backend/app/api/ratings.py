"""
backend/app/api/ratings.py

REST API for ratings management.
Endpoints:
  GET /api/ratings/{media_hash} - Get rating summary
  POST /api/ratings/{media_hash} - Set user rating
"""
from pathlib import Path
import sys
from typing import Optional
import time

from flask import Blueprint, request, jsonify

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from cache_manager import cache
from database_migration import VideoDatabase
from backend.services.ratings_service import RatingsService
from backend.app.api.schemas import RatingInput
from backend.app.core.rate_limiter import get_rate_limiter
from backend.app.admin.performance import get_metrics


ratings_bp = Blueprint('ratings', __name__, url_prefix='/api/ratings')

# Initialize service
_database = VideoDatabase()
ratings_service = RatingsService(cache, _database)
rate_limiter = get_rate_limiter(max_requests=5, window_seconds=10)


def get_client_ip() -> str:
    """Extract client IP from request, handling proxies."""
    # Check X-Forwarded-For header first (for proxies)
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or '127.0.0.1'


def is_lan_origin(origin: str) -> bool:
    """Check if origin is from local network (LAN)."""
    if not origin:
        return False
    
    # Parse origin to get hostname
    try:
        from urllib.parse import urlparse
        parsed = urlparse(origin)
        hostname = parsed.hostname or origin
        
        # Allow localhost and 127.0.0.1
        if hostname in ('localhost', '127.0.0.1', '::1'):
            return True
        
        # Allow 192.168.x.x, 10.x.x.x, 172.16-31.x.x (private networks)
        if hostname.startswith(('192.168.', '10.', '172.')):
            return True
        
        # Allow .local domains (mDNS)
        if hostname.endswith('.local'):
            return True
        
        return False
    except Exception:
        return False


def add_cors_headers(response, origin: Optional[str] = None):
    """Add CORS headers for LAN-only access."""
    origin = origin or request.headers.get('Origin', '')
    
    if is_lan_origin(origin):
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = \
            'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = \
            'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '3600'
    
    return response


@ratings_bp.route('/<path:media_hash>', methods=['OPTIONS'])
def handle_cors_preflight(media_hash: str):
    """Handle CORS preflight requests."""
    response = jsonify({})
    response.status_code = 204
    return add_cors_headers(response)


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
        response = jsonify(summary)
        return add_cors_headers(response)
    except FileNotFoundError as e:
        response = jsonify({"error": str(e)})
        response.status_code = 404
        return add_cors_headers(response)
    except Exception as e:
        response = jsonify({
            "error": "Failed to get rating",
            "detail": str(e)
        })
        response.status_code = 500
        return add_cors_headers(response)


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
    
    Rate Limit: 5 requests per 10 seconds per IP
    Returns 429 if rate limit exceeded
    """
    start_time = time.time()
    
    # Check rate limit
    client_ip = get_client_ip()
    is_allowed, rate_info = rate_limiter.is_allowed(client_ip)

    if not is_allowed:
        response = jsonify({
            "error": "Rate limit exceeded",
            "detail": f"Max 5 requests per 10 seconds. "
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
        response = jsonify({
            "error": "Invalid rating value",
            "detail": str(e)
        })
        response.status_code = 400
        latency = time.time() - start_time
        get_metrics().record_endpoint_latency('POST /api/ratings', latency)
        return add_cors_headers(response)
    except Exception as e:
        # Handle other validation errors
        response = jsonify({
            "error": "Validation failed",
            "detail": str(e)
        })
        response.status_code = 400
        latency = time.time() - start_time
        get_metrics().record_endpoint_latency('POST /api/ratings', latency)
        return add_cors_headers(response)

    try:
        summary = ratings_service.set_rating(media_hash, rating_value)
        response = jsonify(summary)
        response.status_code = 201
        latency = time.time() - start_time
        get_metrics().record_endpoint_latency('POST /api/ratings', latency)
        return add_cors_headers(response)
    except ValueError as e:
        response = jsonify({
            "error": str(e)
        })
        response.status_code = 400
        latency = time.time() - start_time
        get_metrics().record_endpoint_latency('POST /api/ratings', latency)
        return add_cors_headers(response)
    except FileNotFoundError as e:
        response = jsonify({
            "error": str(e)
        })
        response.status_code = 404
        latency = time.time() - start_time
        get_metrics().record_endpoint_latency('POST /api/ratings', latency)
        return add_cors_headers(response)
    except Exception as e:
        response = jsonify({
            "error": "Failed to set rating",
            "detail": str(e)
        })
        response.status_code = 500
        latency = time.time() - start_time
        get_metrics().record_endpoint_latency('POST /api/ratings', latency)
        return add_cors_headers(response)


def register_ratings_api(app):
    """Register ratings API blueprint with Flask app."""
    app.register_blueprint(ratings_bp)
