"""Gallery route blueprint."""

from flask import Blueprint

from backend.app import legacy_runtime as legacy

gallery_bp = Blueprint("gallery", __name__)


@gallery_bp.route("/gallery")
def gallery():
    return legacy.gallery()


@gallery_bp.route("/gallery/image/<path:filename>")
def serve_gallery_image(filename: str):
    return legacy.serve_gallery_image(filename)


@gallery_bp.route("/gallery/groups/<slug>")
def gallery_group(slug: str):
    return legacy.gallery_group(slug)


@gallery_bp.route("/api/gallery", methods=["GET"])
def api_gallery_images():
    return legacy.api_gallery_images()


@gallery_bp.route("/api/gallery/groups", methods=["GET", "POST"])
def api_gallery_groups():
    return legacy.api_gallery_groups()


@gallery_bp.route("/api/similar/<kind>/<path:filename>")
def api_similar(kind: str, filename: str):
    return legacy.api_similar(kind, filename)


@gallery_bp.route("/api/gallery/groups/similar", methods=["POST"])
def api_gallery_group_similar():
    return legacy.api_gallery_group_similar()


@gallery_bp.route("/api/gallery/groups/<int:group_id>/images", methods=["POST"])
def api_add_images_to_group(group_id: int):
    return legacy.api_add_images_to_group(group_id)


@gallery_bp.route("/api/gallery/groups/<int:group_id>/images/<path:image_path>", methods=["DELETE"])
def api_remove_image_from_group(group_id: int, image_path: str):
    return legacy.api_remove_image_from_group(group_id, image_path)


@gallery_bp.route("/api/gallery/groups/<int:group_id>/items/<int:item_id>", methods=["DELETE"])
def api_remove_image_item(group_id: int, item_id: int):
    return legacy.api_remove_image_item(group_id, item_id)


@gallery_bp.route("/api/gallery/groups/<int:group_id>", methods=["PUT", "DELETE"])
def api_modify_group(group_id: int):
    return legacy.api_modify_group(group_id)
