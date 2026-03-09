"""
Recipe API router. Endpoints and request/response models match Android RecipeApi and DTOs.
"""
import logging
from fastapi import APIRouter, HTTPException

from app.schemas.recipe import (
    RecipeResponse,
    IngredientStructuredSchema,
    ImportRecipeRequest,
    NormalizeRecipeRequest,
    TranslateRecipeRequest,
    DetectLanguageRequest,
    DetectLanguageResponse,
)
from app.services.extraction_service import ExtractionService
from app.utils.language import detect_language

logger = logging.getLogger(__name__)

router = APIRouter(tags=["recipe"])
extraction_service = ExtractionService()


@router.post("/import-recipe", response_model=RecipeResponse)
def import_recipe(request: ImportRecipeRequest):
    """
    Import recipe from URL. Validates URL, detects platform, extracts content (demo-safe),
    normalizes and returns RecipeResponse (Android RecipeDto).
    """
    try:
        return extraction_service.import_from_url(request.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Import failed")
        raise HTTPException(status_code=500, detail="Import failed")


@router.post("/normalize-recipe", response_model=RecipeResponse)
def normalize_recipe(body: NormalizeRecipeRequest):
    """
    Normalize raw text (and optional url/title) into RecipeResponse.
    Android sends Map with url, text, source_platform; we accept NormalizeRecipeRequest.
    """
    url = body.url or "https://generic.local/"
    platform = body.source_platform or "generic"
    text = body.text or ""
    title = body.title
    if not text and not title:
        raise HTTPException(status_code=400, detail="Provide 'text' or 'title'")
    try:
        return extraction_service.normalize_from_text(
            url=url,
            platform=platform,
            text=text,
            title=title,
        )
    except Exception as e:
        logger.exception("Normalize failed")
        raise HTTPException(status_code=500, detail="Normalize failed")


@router.post("/detect-language", response_model=DetectLanguageResponse)
def detect_language_endpoint(request: DetectLanguageRequest):
    """Detect language of text. Android expects { language, confidence }."""
    lang, confidence = detect_language(request.text)
    return DetectLanguageResponse(language=lang, confidence=confidence)


@router.post("/translate-recipe", response_model=RecipeResponse)
def translate_recipe(body: TranslateRecipeRequest):
    """
    Accept a recipe-like object and target_language; return recipe (optionally translated).
    Android may send Map with recipe + target_language. We return RecipeResponse.
    """
    recipe = body.recipe if body.recipe is not None else {}
    target = (body.target_language or "it").lower()
    if not recipe:
        raise HTTPException(status_code=400, detail="Provide 'recipe'")
    # Build response from dict; structure matches Android RecipeDto (snake_case)
    raw_structured = recipe.get("ingredients_structured") or []
    ingredients_structured = [
        IngredientStructuredSchema(
            quantity=(item.get("quantity") or "") if isinstance(item, dict) else "",
            unit=(item.get("unit") or "") if isinstance(item, dict) else "",
            name=item.get("name", "") if isinstance(item, dict) else "",
            original_text=(item.get("original_text") or "") if isinstance(item, dict) else "",
        )
        for item in raw_structured
    ]
    return RecipeResponse(
        id=recipe.get("id", 0),
        source_url=recipe.get("source_url", ""),
        source_platform=recipe.get("source_platform", "generic"),
        author=recipe.get("author"),
        title=recipe.get("title", ""),
        cover_image=recipe.get("cover_image"),
        original_language=recipe.get("original_language"),
        translated_language=target,
        ingredients_raw=recipe.get("ingredients_raw") or [],
        ingredients_structured=ingredients_structured,
        steps=recipe.get("steps") or [],
        notes=recipe.get("notes"),
        servings=recipe.get("servings"),
        prep_time_minutes=recipe.get("prep_time_minutes"),
        cook_time_minutes=recipe.get("cook_time_minutes"),
        tags=recipe.get("tags") or [],
        category=recipe.get("category"),
        imported_at=recipe.get("imported_at"),
        is_favorite=recipe.get("is_favorite", False),
    )
