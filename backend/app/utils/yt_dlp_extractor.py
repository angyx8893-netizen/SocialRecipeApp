"""
V5: Extract metadata (title, description/caption, thumbnail) from social links using yt-dlp.
Supports Instagram, TikTok, YouTube, Facebook. No video download; metadata only.
"""
from __future__ import annotations

import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

_YDL_AVAILABLE = False
try:
    import yt_dlp
    _YDL_AVAILABLE = True
except ImportError:
    pass

# Platforms for which yt-dlp is attempted (no download)
_YDL_PLATFORMS = ("instagram", "tiktok", "youtube", "facebook")


def extract_with_yt_dlp(url: str, platform: str) -> Dict[str, Any]:
    """
    Extract title, description, thumbnail from URL using yt-dlp.
    Returns dict: title, description, cover_image (thumbnail URL), success, source='yt-dlp'.
    Description/caption is the main text source for recipe parsing.
    """
    result = {
        "title": None,
        "description": None,
        "cover_image": None,
        "success": False,
        "source": "yt-dlp",
    }
    if not _YDL_AVAILABLE:
        logger.debug("[v5] yt-dlp not installed, skipping")
        return result
    if platform not in _YDL_PLATFORMS:
        return result
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "extract_flat": False,
    }
    try:
        logger.info("[v5] yt-dlp extracting platform=%s url=%s", platform, url[:80])
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        if not info:
            logger.debug("[v5] yt-dlp returned no info")
            return result
        result["title"] = info.get("title") or info.get("fulltitle")
        result["description"] = info.get("description") or info.get("caption")
        thumb = _best_thumbnail(info.get("thumbnails") or [])
        if not thumb and info.get("thumbnail"):
            thumb = info.get("thumbnail")
        result["cover_image"] = thumb
        result["success"] = bool(result["title"] or result["description"] or result["cover_image"])
        logger.info("[v5] yt-dlp success=%s title=%s desc_len=%s thumb=%s",
                    result["success"],
                    (result["title"] or "")[:50],
                    len(result["description"] or ""),
                    "yes" if result["cover_image"] else "no")
    except Exception as e:
        logger.warning("[v5] yt-dlp failed %s: %s", url[:60], e)
    return result


def _best_thumbnail(thumbnails: List[Dict[str, Any]]) -> Optional[str]:
    """Pick best thumbnail URL (prefer thumbnail id or highest resolution)."""
    if not thumbnails:
        return None
    by_preference = sorted(
        thumbnails,
        key=lambda t: (
            0 if t.get("id") in ("thumbnail", "0", "default") else 1,
            -(t.get("height") or 0),
            -(t.get("width") or 0),
        ),
    )
    for t in by_preference:
        url = t.get("url")
        if url and url.startswith(("http://", "https://")):
            return url
    return None
