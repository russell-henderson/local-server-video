"""Archived app_subs_integration shim (historical copy).

This file previously registered Flask routes and template helpers for
the subtitle system. Kept as an archived reference.
"""
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def register_subtitle_routes(app) -> None:
    """No-op (archived copy)."""
    logger.debug("Archived: register_subtitle_routes called but does nothing.")


def lazy_subtitle_check(video_path: str) -> Dict[str, object]:
    return {"has_subtitles": False, "video_path": video_path}


def enhance_video_context(video_info: dict) -> dict:
    ctx = dict(video_info or {})
    ctx.update(lazy_subtitle_check(ctx.get("path", "")))
    return ctx
