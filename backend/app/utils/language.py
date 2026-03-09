"""Language detection (with confidence). Translation can be plugged in (e.g. external API)."""
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

try:
    from langdetect import detect, detect_langs, DetectorFactory
    DetectorFactory.seed = 0
    _LANG_AVAILABLE = True
except ImportError:
    _LANG_AVAILABLE = False


def detect_language(text: str) -> Tuple[str, float]:
    """
    Detect language code and confidence. Returns (lang_code, confidence in 0..1).
    Uses detect_langs for confidence when available.
    """
    if not text or not _LANG_AVAILABLE:
        return "en", 0.0
    try:
        langs = detect_langs(text)
        if langs:
            top = langs[0]
            return top.lang, float(top.prob)
        lang = detect(text)
        return lang, 0.85
    except Exception as e:
        logger.warning("Language detection failed: %s", e)
        return "en", 0.0


def translate_to_italian(text: str) -> str:
    """
    Translate text to Italian. Default: no-op (return as-is).
    Replace with real translator (e.g. Google Translate API, LibreTranslate) when needed.
    """
    if not text:
        return text
    return text
