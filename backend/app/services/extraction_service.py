"""
V5 Recipe extraction pipeline.
- yt-dlp for Instagram/TikTok/YouTube/Facebook (title, description, thumbnail); OpenGraph fallback.
- Description/caption as main recipe text source; no placeholder fallback.
- Heuristic ingredient/step detection; language detection and translation to Italian when needed.
- Structured response: title, cover_image, raw_extracted_text, ingredients_raw, ingredients_structured, steps.
- Debug logging: platform, metadata, cleaned text, parsed ingredients, parsed steps.
"""
import logging
import time
from typing import Optional, List, Tuple

from app.schemas.recipe import (
    RecipeResponse,
    IngredientStructuredSchema,
)
from app.utils.url_parser import validate_url, detect_platform
from app.utils.text_parser import (
    clean_recipe_text,
    rank_text_sources,
    extract_recipe_sections,
    parse_ingredient_line,
    filter_ingredients_by_confidence,
    infer_tags,
)
from app.utils.metadata_fetcher import fetch_metadata, select_cover_image
from app.services.language_service import detect_language, translate_recipe_to_italian

logger = logging.getLogger(__name__)

INGREDIENT_MIN_CONFIDENCE = 0.55
DEBUG_TEXT_SNIPPET_LEN = 300


class ExtractionService:
    """
    V5: Extracts recipe from URL using yt-dlp or OpenGraph.
    Uses description/caption as main text. Returns empty lists when no recipe detected.
    """

    def import_from_url(self, url: str) -> RecipeResponse:
        """Validate URL, fetch metadata (yt-dlp or OG), parse description as recipe. No placeholder."""
        ok, err = validate_url(url)
        if not ok:
            raise ValueError(err)
        platform = detect_platform(url)
        logger.info("[v5] source_platform=%s url=%s", platform, url[:80])

        metadata = fetch_metadata(url, platform)
        logger.info("[v5] extracted_metadata source=%s success=%s title=%s desc_len=%s has_thumb=%s",
                    metadata.get("source"), metadata.get("success"),
                    (metadata.get("title") or "")[:50],
                    len(metadata.get("description") or ""),
                    "yes" if metadata.get("cover_image") else "no")

        raw_text = self._gather_text_for_recipe(platform, metadata)
        logger.info("[v5] text_gather raw_len=%d (no placeholder)", len(raw_text or ""))

        cover_url = select_cover_image(metadata, url)
        cover_source = metadata.get("source") or ("og:image" if cover_url else None)

        return self._normalize_to_recipe(
            url=url,
            platform=platform,
            raw_text=raw_text or "",
            title_override=metadata.get("title"),
            cover_image=cover_url,
            cover_image_source=cover_source,
            raw_extracted=raw_text,
        )

    def _gather_text_for_recipe(self, platform: str, metadata: dict) -> str:
        """Use description/caption as main recipe text source. No placeholder."""
        sources: List[Tuple[str, str]] = []
        desc = metadata.get("description")
        if desc and desc.strip():
            sources.append((desc.strip(), "metadata"))
        title = metadata.get("title")
        if title and title.strip():
            sources.append((title.strip(), "metadata"))
        raw_html = metadata.get("raw_text") or ""
        if raw_html and len(raw_html) > 100:
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(raw_html, "html.parser")
                body = soup.find("body")
                if body:
                    body_text = body.get_text(separator="\n", strip=True)
                    if body_text and len(body_text) > 50:
                        sources.append((body_text[:15000], "body"))
            except Exception as e:
                logger.debug("[v5] body extract failed: %s", e)
        if not sources:
            return ""
        return rank_text_sources(sources) or ""

    def _normalize_to_recipe(
        self,
        url: str,
        platform: str,
        raw_text: str,
        title_override: Optional[str] = None,
        cover_image: Optional[str] = None,
        cover_image_source: Optional[str] = None,
        raw_extracted: Optional[str] = None,
    ) -> RecipeResponse:
        """
        Parse into structured recipe. Heuristic ingredient/step detection.
        No placeholder recipes; ingredient lines are never copied into steps.
        If no recipe detected: empty ingredients and steps; still return rawText and parsing_confidence.
        """
        logger.info("[v5] raw_extracted_text length=%d snippet=%s", len(raw_text or ""), ((raw_text or "")[:DEBUG_TEXT_SNIPPET_LEN] + "..." if len(raw_text or "") > DEBUG_TEXT_SNIPPET_LEN else (raw_text or "")))
        cleaned = clean_recipe_text(raw_text)
        logger.info("[v5] cleaned_text length=%d snippet=%s", len(cleaned), (cleaned[:DEBUG_TEXT_SNIPPET_LEN] + "..." if len(cleaned) > DEBUG_TEXT_SNIPPET_LEN else cleaned))

        sections = extract_recipe_sections(cleaned)
        title = title_override or sections.get("title") or f"Recipe from {platform}"
        raw_ingredient_lines = sections.get("ingredients") or []
        steps = sections.get("steps") or []

        det_ing = sections.get("ingredients_section") or ""
        det_steps = sections.get("steps_section") or ""
        logger.info("[v5] detected_ingredients_section length=%d snippet=%s", len(det_ing), (det_ing[:250] + "..." if len(det_ing) > 250 else det_ing))
        logger.info("[v5] detected_steps_section length=%d snippet=%s", len(det_steps), (det_steps[:250] + "..." if len(det_steps) > 250 else det_steps))

        filtered = filter_ingredients_by_confidence(
            raw_ingredient_lines, min_confidence=INGREDIENT_MIN_CONFIDENCE
        )
        ingredients_raw = [line for line, _ in filtered]
        ingredients_structured: List[IngredientStructuredSchema] = []
        for line in ingredients_raw:
            q, u, n, orig, _ = parse_ingredient_line(line)
            ingredients_structured.append(
                IngredientStructuredSchema(quantity=q or "", unit=u or "", name=n or line, original_text=orig or line)
            )

        logger.info("[v5] parsed_ingredients count=%d list=%s", len(ingredients_structured), ingredients_raw[:15])
        logger.info("[v5] parsed_steps count=%d list=%s", len(steps), [s[:60] for s in steps[:10]])

        has_recipe = bool(ingredients_structured or steps)
        parsing_confidence = (
            min(0.95, 0.5 + 0.1 * len(ingredients_structured) + 0.05 * len(steps))
            if has_recipe else 0.0
        )

        sample = f"{title} {' '.join(ingredients_raw[:3])} {' '.join(steps[:2])}"
        lang, lang_confidence = detect_language(sample)
        logger.info("[v5] detected_language=%s confidence=%.2f", lang, lang_confidence)

        translated_language = None
        if lang != "it" and has_recipe:
            try:
                title, ingredients_raw, steps, ingredients_structured = translate_recipe_to_italian(
                    title, ingredients_raw, steps, ingredients_structured, lang, lang_confidence
                )
                translated_language = "it"
                logger.info("[v5] translation applied -> Italian")
            except Exception as e:
                logger.warning("[v5] translation skipped: %s", e)

        tags = infer_tags(cleaned) if cleaned else []
        return RecipeResponse(
            id=0,
            source_url=url,
            source_platform=platform,
            author=None,
            title=title,
            cover_image=cover_image,
            original_language=lang,
            translated_language=translated_language,
            ingredients_raw=ingredients_raw,
            ingredients_structured=ingredients_structured,
            steps=steps,
            notes=None,
            servings=None,
            prep_time_minutes=None,
            cook_time_minutes=None,
            tags=tags,
            category="General" if has_recipe else None,
            imported_at=int(time.time()),
            is_favorite=False,
            raw_extracted_text=(raw_extracted[:2000] if raw_extracted else None),
            cleaned_text=(cleaned[:2000] if cleaned else None),
            parsing_confidence=round(parsing_confidence, 2),
            cover_image_source=cover_image_source,
        )

    def normalize_from_text(
        self,
        url: str = "https://generic.local/",
        platform: str = "generic",
        text: str = "",
        title: Optional[str] = None,
    ) -> RecipeResponse:
        """Normalize raw text into RecipeResponse. No placeholder."""
        if not text and not title:
            text = ""
        cleaned = clean_recipe_text(text) if text else ""
        return self._normalize_to_recipe(
            url=url,
            platform=platform,
            raw_text=cleaned or text,
            title_override=title,
            cover_image=None,
            cover_image_source=None,
            raw_extracted=text,
        )
