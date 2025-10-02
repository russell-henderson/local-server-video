# app_subs_integration.py
from flask import jsonify

from subtitles import has_any_subs, generate_for_file


def register_subtitle_routes(app):
    """Register subtitle routes with the Flask app."""
    
    @app.route("/api/subtitles/<path:video_path>", methods=["GET"])
    def subtitle_status_api(video_path):
        """API endpoint to get subtitle status."""
        if not video_path:
            return jsonify({"error": "No video path provided"}), 400

        full_path = f"videos/{video_path}"
        has_subs = has_any_subs(full_path)
        return jsonify({
            "video": video_path,
            "has_subtitles": has_subs
        })

    @app.route("/api/subtitles/<path:video_path>", methods=["POST"])
    def generate_subtitle_sync_api(video_path):
        """API endpoint to trigger synchronous subtitle generation."""
        if not video_path:
            return jsonify({"error": "No video path provided"}), 400

        full_path = f"videos/{video_path}"

        try:
            result = generate_for_file(full_path)
            return jsonify({
                "status": "generated",
                "result": result
            })
        except FileNotFoundError as e:
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 404
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500

    # Template helper function
    @app.template_global()
    def subtitle_status_global(video_path: str) -> dict:
        """Template function to check subtitle status."""
        return lazy_subtitle_check(video_path)


def lazy_subtitle_check(video_path: str) -> dict:
    """
    Check if subtitles exist, return status info.
    Used by templates to show subtitle availability.
    """
    has_subs = has_any_subs(video_path)
    return {
        "has_subtitles": has_subs,
        "video_path": video_path
    }


# Add subtitle info to video context
def enhance_video_context(video_info: dict) -> dict:
    """Add subtitle information to video context."""
    video_path = video_info.get("path", "")
    subtitle_info = lazy_subtitle_check(video_path)
    video_info.update(subtitle_info)
    return video_info
