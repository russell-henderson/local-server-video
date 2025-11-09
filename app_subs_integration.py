"""app_subs_integration.py — subtitle integration removed (compat shim)

This module used to register Flask routes and template helpers for the
automatic subtitle generation system. That feature has been removed.
To avoid ImportError and to keep template/context calls safe, this file
provides small, safe no-op helpers. No Flask routes are registered.
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


def register_subtitle_routes(app) -> None:
    """No-op: subtitle routes removed.

    Keep the function present so code that calls
    `app_subs_integration.register_subtitle_routes(app)` won't fail,
    but don't register any endpoints.
    """
    logger.debug(
        "Subtitle routes removed: register_subtitle_routes is a no-op."
    )


def lazy_subtitle_check(video_path: str) -> Dict[str, object]:
    """Return a safe subtitle status dict (always no subtitles).

    This lets templates call the helper without importing the heavy
    subtitle backend.
    """
    return {"has_subtitles": False, "video_path": video_path}


def enhance_video_context(video_info: dict) -> dict:
    """Add safe subtitle info to the provided video context dict.

    Returns a new dict with `has_subtitles` set to False.
    """
    ctx = dict(video_info or {})
    ctx.update(lazy_subtitle_check(ctx.get("path", "")))
    return ctx
