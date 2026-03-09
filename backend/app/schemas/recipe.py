"""
V5 Recipe API schemas. Field names match Android DTOs (snake_case).
Response shape: title, cover_image, raw_extracted_text, ingredients_raw, ingredients_structured, steps.
Structured ingredients support shopping list: quantity, unit, name, original_text.
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class IngredientStructuredSchema(BaseModel):
    """
    Structured ingredient for shopping list.
    - quantity: e.g. "200", "2", or ""
    - unit: e.g. "g", "cucchiai", or ""
    - name: ingredient name (e.g. "pasta tipo calamarata", "patate", "sale")
    - original_text: full original line when parsing is uncertain (always set)
    """
    quantity: str = ""
    unit: str = ""
    name: str
    original_text: str = ""


class RecipeResponse(BaseModel):
    """
    V5 structured response: title, cover_image, raw_extracted_text, ingredients, steps.
    When no recipe is detected: empty ingredients/steps, raw_extracted_text and parsing_confidence still set.
    """
    id: Optional[int] = 0
    source_url: str
    source_platform: str
    author: Optional[str] = None
    title: str
    cover_image: Optional[str] = None
    original_language: Optional[str] = None
    translated_language: Optional[str] = None
    ingredients_raw: List[str] = Field(default_factory=list)
    ingredients_structured: List[IngredientStructuredSchema] = Field(default_factory=list)
    steps: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    servings: Optional[int] = None
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    imported_at: Optional[int] = None
    is_favorite: bool = False
    raw_extracted_text: Optional[str] = None
    cleaned_text: Optional[str] = None
    parsing_confidence: Optional[float] = None
    cover_image_source: Optional[str] = None

    model_config = {"populate_by_name": True}


class ImportRecipeRequest(BaseModel):
    url: str


class NormalizeRecipeRequest(BaseModel):
    url: Optional[str] = None
    text: Optional[str] = None
    source_platform: Optional[str] = "generic"
    title: Optional[str] = None


class TranslateRecipeRequest(BaseModel):
    recipe: Optional[dict] = None
    target_language: str = "it"


class DetectLanguageRequest(BaseModel):
    text: str


class DetectLanguageResponse(BaseModel):
    language: str
    confidence: Optional[float] = None


class HealthResponse(BaseModel):
    status: str = "ok"
