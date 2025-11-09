"""Compact compatibility stub for app_subs_integration.

The fuller archived copy is available at
`archive/python_legacy/app_subs_integration.py`.
"""

import logging
import warnings
from typing import Dict

warnings.warn(
    "app_subs_integration archived to archive/python_legacy/app_subs_integration.py",
    DeprecationWarning,
)

logger = logging.getLogger(__name__)


def register_subtitle_routes(app) -> None:
    """No-op: preserve call-site compatibility."""
    logger.debug("Archived: register_subtitle_routes is a no-op.")


def lazy_subtitle_check(video_path: str) -> Dict[str, object]:
    return {"has_subtitles": False, "video_path": video_path}


def enhance_video_context(video_info: dict) -> dict:
    ctx = dict(video_info or {})
    ctx.update(lazy_subtitle_check(ctx.get("path", "")))
    return ctx
