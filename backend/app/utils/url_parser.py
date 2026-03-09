"""URL validation and platform detection. Aligns with supported sources (Instagram, TikTok, etc.)."""
from urllib.parse import urlparse
from typing import Tuple


def validate_url(url: str) -> Tuple[bool, str]:
    """
    Validate URL format. Returns (ok, error_message).
    """
    if not url or not isinstance(url, str):
        return False, "URL is required"
    url = url.strip()
    if not url:
        return False, "URL is required"
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False, "URL must use http or https"
        if not parsed.netloc:
            return False, "Invalid URL host"
        return True, ""
    except Exception as e:
        return False, f"Invalid URL: {e}"


def detect_platform(url: str) -> str:
    """
    Detect source platform from URL. Returns lowercase identifier.
    Matches Android expectation: instagram, tiktok, facebook, youtube, generic.
    """
    url_lower = url.lower()
    if "instagram.com" in url_lower or "instagr.am" in url_lower:
        return "instagram"
    if "tiktok.com" in url_lower or "vm.tiktok.com" in url_lower:
        return "tiktok"
    if "facebook.com" in url_lower or "fb.com" in url_lower or "fb.watch" in url_lower:
        return "facebook"
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "youtube"
    return "generic"
