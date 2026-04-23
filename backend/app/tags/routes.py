"""Tags route blueprint."""

from flask import Blueprint

from backend.app import legacy_runtime as legacy

tags_bp = Blueprint("tags", __name__)


@tags_bp.route("/tag", methods=["POST"])
def add_tag():
    return legacy.add_tag()


@tags_bp.route("/delete_tag", methods=["POST"])
def delete_tag():
    return legacy.delete_tag()


@tags_bp.route("/api/tags/popular")
def popular_tags_api():
    return legacy.popular_tags_api()


@tags_bp.route("/api/tags/video")
def video_tags_api():
    return legacy.video_tags_api()


@tags_bp.route("/tags")
def tags_page():
    return legacy.tags_page()


@tags_bp.route("/tag/<tag>")
def tag_videos(tag: str):
    return legacy.tag_videos(tag)
