"""
V5: Language detection and translation to Italian when needed.
Only translate when confidence is high to avoid bad Italian from noisy text.
"""
import logging
from typing import List, Tuple

from app.schemas.recipe import IngredientStructuredSchema
from app.utils.language import detect_language as _detect, translate_to_italian as _translate

logger = logging.getLogger(__name__)

TRANSLATE_MIN_CONFIDENCE = 0.7


def detect_language(text: str) -> Tuple[str, float]:
    """Detect language of text. Returns (language_code, confidence)."""
    return _detect(text)


def translate_recipe_to_italian(
    title: str,
    ingredients_raw: List[str],
    steps: List[str],
    ingredients_structured: List[IngredientStructuredSchema],
    lang: str,
    confidence: float,
) -> Tuple[str, List[str], List[str], List[IngredientStructuredSchema]]:
    """
    Translate recipe to Italian when source is not Italian and confidence >= threshold.
    Returns (title, ingredients_raw, steps, ingredients_structured).
    """
    if lang == "it":
        logger.debug("[v5] translation skip: already Italian")
        return title, ingredients_raw, steps, ingredients_structured
    if confidence < TRANSLATE_MIN_CONFIDENCE:
        logger.debug("[v5] translation skip: confidence %.2f < %.2f", confidence, TRANSLATE_MIN_CONFIDENCE)
        return title, ingredients_raw, steps, ingredients_structured
    try:
        title_t = _translate(title)
        ingredients_t = [_translate(i) for i in ingredients_raw]
        steps_t = [_translate(s) for s in steps]
        structured_t = [
            IngredientStructuredSchema(
                quantity=ing.quantity or "",
                unit=ing.unit or "",
                name=_translate(ing.name),
                original_text=ing.original_text or ing.name,
            )
            for ing in ingredients_structured
        ]
        logger.info("[v5] translated to Italian: %d ingredients, %d steps", len(structured_t), len(steps_t))
        return title_t, ingredients_t, steps_t, structured_t
    except Exception as e:
        logger.warning("[v5] translation failed, keeping original: %s", e)
        return title, ingredients_raw, steps, ingredients_structured
