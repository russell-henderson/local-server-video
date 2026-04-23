"""Application factory and blueprint registration."""

from pathlib import Path
from flask import Flask

from backend.app.api.ratings import register_ratings_api
from backend.app.admin.routes import register_admin_routes
from backend.app.gallery.routes import gallery_bp
from backend.app.media.routes import media_bp
from backend.app.metadata.routes import metadata_bp
from backend.app.tags.routes import tags_bp
from backend.app import legacy_runtime as legacy


def create_app() -> Flask:
    """Build the Flask app with full route-family blueprints."""
    repo_root = Path(__file__).resolve().parents[2]
    app = Flask(
        __name__,
        template_folder=str(repo_root / "templates"),
        static_folder=str(repo_root / "static"),
        root_path=str(repo_root),
    )
    app.register_blueprint(media_bp)
    app.register_blueprint(tags_bp)
    app.register_blueprint(gallery_bp)
    app.register_blueprint(metadata_bp)
    register_ratings_api(app)
    register_admin_routes(app)

    # Keep startup side-effects and request hooks from legacy runtime.
    app.before_request(legacy._perf_log_before_request)
    app.after_request(legacy._perf_log_after_request)
    app.teardown_appcontext(legacy.cleanup)

    # Preserve legacy endpoint names used in templates/url_for calls.
    app.add_url_rule("/ping", endpoint="ping", view_func=legacy.ping)
    app.add_url_rule("/favicon.ico", endpoint="favicon", view_func=legacy.favicon)
    app.add_url_rule("/", endpoint="index", view_func=legacy.index)
    app.add_url_rule("/watch/<path:filename>", endpoint="watch_video", view_func=legacy.watch_video)
    app.add_url_rule("/popular", endpoint="popular_page", view_func=legacy.popular_page)
    app.add_url_rule("/video/<path:filename>", endpoint="stream_video", view_func=legacy.stream_video)
    app.add_url_rule("/get_views", endpoint="get_views_route", view_func=legacy.get_views_route)
    app.add_url_rule("/rate", endpoint="rate_video", view_func=legacy.rate_video, methods=["POST"])
    app.add_url_rule("/view", endpoint="record_view", view_func=legacy.record_view, methods=["POST"])
    app.add_url_rule("/tag", endpoint="add_tag", view_func=legacy.add_tag, methods=["POST"])
    app.add_url_rule("/delete_tag", endpoint="delete_tag", view_func=legacy.delete_tag, methods=["POST"])
    app.add_url_rule("/api/tags/popular", endpoint="popular_tags_api", view_func=legacy.popular_tags_api)
    app.add_url_rule("/api/tags/video", endpoint="video_tags_api", view_func=legacy.video_tags_api)
    app.add_url_rule("/favorite", endpoint="toggle_favorite", view_func=legacy.toggle_favorite, methods=["POST"])
    app.add_url_rule("/favorites", endpoint="favorites_page", view_func=legacy.favorites_page)
    app.add_url_rule("/random", endpoint="random_video", view_func=legacy.random_video)
    app.add_url_rule("/tags", endpoint="tags_page", view_func=legacy.tags_page)
    app.add_url_rule("/tag/<tag>", endpoint="tag_videos", view_func=legacy.tag_videos)
    app.add_url_rule("/best-of", endpoint="best_of", view_func=legacy.best_of)
    app.add_url_rule("/links", endpoint="links", view_func=legacy.links)
    app.add_url_rule("/search", endpoint="search_page", view_func=legacy.search_page)
    app.add_url_rule("/gallery", endpoint="gallery", view_func=legacy.gallery)
    app.add_url_rule("/gallery/image/<path:filename>", endpoint="serve_gallery_image", view_func=legacy.serve_gallery_image)
    app.add_url_rule("/gallery/groups/<slug>", endpoint="gallery_group", view_func=legacy.gallery_group)
    app.add_url_rule("/api/gallery", endpoint="api_gallery_images", view_func=legacy.api_gallery_images, methods=["GET"])
    app.add_url_rule("/api/gallery/groups", endpoint="api_gallery_groups", view_func=legacy.api_gallery_groups, methods=["GET", "POST"])
    app.add_url_rule("/api/similar/<kind>/<path:filename>", endpoint="api_similar", view_func=legacy.api_similar)
    app.add_url_rule("/api/gallery/groups/similar", endpoint="api_gallery_group_similar", view_func=legacy.api_gallery_group_similar, methods=["POST"])
    app.add_url_rule("/api/gallery/groups/<int:group_id>/images", endpoint="api_add_images_to_group", view_func=legacy.api_add_images_to_group, methods=["POST"])
    app.add_url_rule("/api/gallery/groups/<int:group_id>/images/<path:image_path>", endpoint="api_remove_image_from_group", view_func=legacy.api_remove_image_from_group, methods=["DELETE"])
    app.add_url_rule("/api/gallery/groups/<int:group_id>/items/<int:item_id>", endpoint="api_remove_image_item", view_func=legacy.api_remove_image_item, methods=["DELETE"])
    app.add_url_rule("/api/gallery/groups/<int:group_id>", endpoint="api_modify_group", view_func=legacy.api_modify_group, methods=["PUT", "DELETE"])
    app.add_url_rule("/admin/cache/status", endpoint="cache_status", view_func=legacy.cache_status)
    app.add_url_rule("/admin/cache/refresh", endpoint="refresh_cache", view_func=legacy.refresh_cache, methods=["POST"])
    app.add_url_rule("/admin/metadata/prune", endpoint="admin_metadata_prune", view_func=legacy.admin_metadata_prune, methods=["POST"])
    app.add_url_rule("/analytics/save", endpoint="save_analytics", view_func=legacy.save_analytics, methods=["POST"])
    app.add_url_rule("/analytics/get/<path:filename>", endpoint="get_analytics", view_func=legacy.get_analytics)
    app.add_url_rule("/analytics/export", endpoint="export_analytics", view_func=legacy.export_analytics)
    app.add_url_rule("/analytics/stats", endpoint="analytics_stats", view_func=legacy.analytics_stats)

    return app
