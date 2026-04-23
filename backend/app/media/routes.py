"""Media route blueprint."""

from flask import Blueprint

from backend.app import legacy_runtime as legacy

media_bp = Blueprint("media", __name__)


@media_bp.route("/ping")
def ping():
    return legacy.ping()


@media_bp.route("/favicon.ico")
def favicon():
    return legacy.favicon()


@media_bp.route("/")
def index():
    return legacy.index()


@media_bp.route("/watch/<path:filename>")
def watch_video(filename: str):
    return legacy.watch_video(filename)


@media_bp.route("/popular")
def popular_page():
    return legacy.popular_page()


@media_bp.route("/video/<path:filename>")
def stream_video(filename: str):
    return legacy.stream_video(filename)


@media_bp.route("/get_views")
def get_views_route():
    return legacy.get_views_route()


@media_bp.route("/rate", methods=["POST"])
def rate_video():
    return legacy.rate_video()


@media_bp.route("/view", methods=["POST"])
def record_view():
    return legacy.record_view()


@media_bp.route("/favorite", methods=["POST"])
def toggle_favorite():
    return legacy.toggle_favorite()


@media_bp.route("/favorites")
def favorites_page():
    return legacy.favorites_page()


@media_bp.route("/random")
def random_video():
    return legacy.random_video()


@media_bp.route("/best-of")
def best_of():
    return legacy.best_of()


@media_bp.route("/links")
def links():
    return legacy.links()


@media_bp.route("/search")
def search_page():
    return legacy.search_page()
