"""
V5: Metadata extraction for recipe import.
yt-dlp for Instagram/TikTok/YouTube/Facebook → title, description/caption, thumbnail.
OpenGraph fallback → og:title, og:description, og:image.
Description/caption is the main recipe text source.
"""
from __future__ import annotations

import logging
import re
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin, urlparse

from app.utils.yt_dlp_extractor import extract_with_yt_dlp
from app.utils.url_parser import detect_platform

logger = logging.getLogger(__name__)

try:
    import requests
    from bs4 import BeautifulSoup
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SocialRecipeBot/1.0)",
    "Accept": "text/html,application/xhtml+xml",
}
_TIMEOUT = 10


def fetch_metadata(url: str, platform: Optional[str] = None) -> Dict[str, Any]:
    """
    V5: Fetch metadata for recipe extraction.
    1. Instagram, TikTok, YouTube, Facebook: try yt-dlp (title, description, thumbnail).
    2. OpenGraph fallback: og:title, og:description, og:image.
    Returns: title, description, cover_image, raw_text, success, source.
    """
    platform = platform or detect_platform(url)
    result = {
        "title": None,
        "description": None,
        "cover_image": None,
        "raw_text": "",
        "success": False,
        "source": None,
    }

    if platform in ("instagram", "tiktok", "youtube", "facebook"):
        logger.info("[v5] metadata: trying yt-dlp platform=%s", platform)
        ydl_result = extract_with_yt_dlp(url, platform)
        if ydl_result.get("success"):
            result["title"] = ydl_result.get("title")
            result["description"] = ydl_result.get("description")
            result["cover_image"] = ydl_result.get("cover_image")
            result["success"] = True
            result["source"] = "yt-dlp"
            logger.info("[v5] metadata: yt-dlp ok title=%s desc_len=%s",
                        (result["title"] or "")[:40], len(result["description"] or ""))
            return result
        logger.debug("[v5] metadata: yt-dlp failed, OpenGraph fallback")

    logger.info("[v5] metadata: OpenGraph fallback url=%s", url[:80])
    og = _fetch_opengraph(url)
    result["title"] = result["title"] or og.get("title")
    result["description"] = result["description"] or og.get("description")
    result["cover_image"] = result["cover_image"] or og.get("cover_image")
    result["raw_text"] = og.get("raw_text") or ""
    if result["title"] or result["description"] or result["cover_image"]:
        result["success"] = True
        if not result["source"]:
            result["source"] = "opengraph"
    return result


def _fetch_opengraph(url: str) -> Dict[str, Any]:
    """Fetch page and extract og:title, og:description, og:image."""
    out = {"title": None, "description": None, "cover_image": None, "raw_text": ""}
    if not _REQUESTS_AVAILABLE:
        return out
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        text = resp.text
        out["raw_text"] = text
        soup = BeautifulSoup(text, "html.parser")
        og_title = _tag_content(soup, "meta", {"property": "og:title"})
        og_desc = _tag_content(soup, "meta", {"property": "og:description"})
        og_image = _tag_content(soup, "meta", {"property": "og:image"}) or _tag_content(soup, "meta", {"property": "og:image:url"})
        out["title"] = og_title or _tag_content(soup, "meta", {"name": "title"})
        if not out["title"] and soup.title:
            out["title"] = soup.title.get_text(strip=True) if soup.title else None
        out["description"] = og_desc or _tag_content(soup, "meta", {"name": "description"})
        out["cover_image"] = _resolve_image_url(og_image, url)
        if not out["cover_image"]:
            for meta in soup.find_all("meta", property=re.compile(r"og:image")):
                c = meta.get("content")
                if c:
                    out["cover_image"] = _resolve_image_url(c, url)
                    break
        if not out["cover_image"]:
            for img in soup.find_all("img", src=True):
                src = img.get("src")
                if src and not src.startswith("data:"):
                    out["cover_image"] = _resolve_image_url(src, url)
                    break
    except Exception as e:
        logger.debug("[v5] OpenGraph fetch failed: %s", e)
    return out


def _tag_content(soup, tag: str, attrs: dict) -> Optional[str]:
    el = soup.find(tag, attrs)
    if el and el.get("content"):
        return el["content"].strip()
    return None


def _resolve_image_url(href: Optional[str], base: str) -> Optional[str]:
    if not href or not href.strip():
        return None
    href = href.strip()
    if href.startswith("//"):
        href = "https:" + href
    if not href.startswith(("http://", "https://")):
        href = urljoin(base, href)
    try:
        p = urlparse(href)
        if p.scheme in ("http", "https") and p.netloc:
            return href
    except Exception:
        pass
    return None


def select_cover_image(metadata: Dict[str, Any], url: str) -> Optional[str]:
    """Return cover image URL (yt-dlp thumbnail or og:image)."""
    return metadata.get("cover_image")
