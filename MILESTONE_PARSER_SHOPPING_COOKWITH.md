# SocialRecipeApp – Parser, Structured Ingredients, Shopping List, Cook with What I Have

This document summarizes the milestone: parser fix, structured ingredients, shopping list support, and "Cook with what I have".

---

## A. Parser fix

**Backend: `backend/app/utils/text_parser.py`**

- **Section detection:** Headers for ingredients (ingredienti, ingredients, …) and steps (procedimento, preparazione, instructions, steps, method, …). `split_into_sections()` returns `ingredients_section` and `steps_section`; header lines are never included in section content.
- **No duplication:** Ingredients are parsed only from `ingredients_section`; steps only from `steps_section`. `extract_ordered_steps()` takes `exclude_ingredient_lines` so ingredient lines are never copied into steps. Deduplication uses normalized line comparison.
- **Cooking verbs when steps missing:** If `steps_section` is empty, `_steps_from_text_by_verbs()` finds lines with cooking verbs (cuoci, taglia, mescola, aggiungi, versa, frulla, rosola, scola, inforna, mix, cook, stir, add, bake, …) and numbered steps, excluding any line that matches the ingredient set.
- **Output:** `extract_recipe_sections()` returns clean `ingredients` and `steps` lists; no placeholder data.

**Backend: `backend/app/services/extraction_service.py`**

- Uses `extract_recipe_sections()`; returns `ingredients_raw`, `ingredients_structured`, `steps` in `RecipeResponse`. No placeholder fallback.

---

## B. Structured ingredients

**Backend: `backend/app/schemas/recipe.py`**

- `IngredientStructuredSchema`: `quantity`, `unit`, `name`, `original_text` (all strings; empty string when absent).
- `RecipeResponse`: `ingredients_raw`, `ingredients_structured`, `steps`.

**Backend: `backend/app/utils/text_parser.py`**

- `parse_ingredient_line()` returns `(quantity, unit, name, original_text, confidence)`.
- Supports Italian "di" (e.g. "200 g di pasta tipo calamarata") and common units: g, kg, ml, l, cucchiaio, cucchiai, cucchiaino, cucchiaini, cup, cups, tsp, tbsp, fetta, fette, noce, noci, etc.
- Original line is always preserved as `original_text`.

**Backend: `backend/app/services/language_service.py`**

- When translating to Italian, structured ingredients keep `quantity`, `unit`, `original_text`; only `name` is translated.

**Android**

- `domain/model/IngredientStructured.kt`: `quantity`, `unit`, `name`, `originalText`.
- `data/remote/dto/RecipeDto.kt`: `IngredientStructuredDto` with `original_text` (SerializedName).
- `data/mapper/RecipeMappers.kt`: maps `originalText` ↔ `original_text`.
- `domain/model/Recipe.kt`, `data/local/entity/RecipeEntity.kt`: both have `ingredientsRaw` and `ingredientsStructured` (JSON for entity).

---

## C. Shopping list support

**Android**

- `ui/screens/detail/RecipeDetailViewModel.kt`: `addAllToShoppingList()` uses `ingredientsStructured`; for each ingredient uses `originalText` when non-blank for the item name, else builds from quantity + unit + name; passes `ing.quantity` and `ing.unit` to `ShoppingItem`.
- `ui/screens/detail/RecipeDetailScreen.kt`: Displays ingredients using `originalText` when present, else quantity + unit + name.
- `ui/screens/shopping/ShoppingListScreen.kt`: Shows each item with quantity, unit, name (already supported by `ShoppingItem`).
- `domain/model/ShoppingItem.kt`, `data/local/entity/ShoppingItemEntity.kt`: `name`, `quantity`, `unit`; no schema change.

---

## D. Cook with what I have

**Android (all logic on device)**

- `domain/model/RecipeMatchResult.kt`: `recipe`, `matchPercentage`, `matchedIngredients`, `missingIngredients`.
- `ui/screens/cookwith/CookWithWhatIHaveViewModel.kt`:
  - Input: one ingredient per line; normalized (lowercase, trim, remove filler words: di, da, per, the, and, …).
  - Uses `recipe.ingredientsStructured` and `ing.name` for matching; fallback to `ingredientsRaw` if no structured list.
  - Match: recipe ingredient is matched if any user normalized token is substring of normalized recipe ingredient name or vice versa.
  - Computes matched list, missing list, match percentage; sorts by percentage descending; only recipes with at least one match.
- `ui/screens/cookwith/CookWithWhatIHaveScreen.kt`: Multiline input (one per line), match cards with title, X% match, "You have: …", "Missing: …", tap opens recipe detail.

---

## E. Quality

- **Compile-safe:** Backend (Python) and Android (Kotlin) are consistent; no API change beyond existing `ingredients_raw` / `ingredients_structured` / `steps`.
- **Models aligned:** Backend `quantity`, `unit`, `name`, `original_text` ↔ Android `IngredientStructured` / `IngredientStructuredDto` with `original_text` SerializedName.

---

## File index (full corrected files in repo)

| Layer        | File |
|-------------|------|
| Backend     | `backend/app/utils/text_parser.py` |
| Backend     | `backend/app/schemas/recipe.py` |
| Backend     | `backend/app/services/extraction_service.py` |
| Backend     | `backend/app/services/language_service.py` |
| Android     | `app/.../domain/model/IngredientStructured.kt` |
| Android     | `app/.../domain/model/Recipe.kt` |
| Android     | `app/.../domain/model/RecipeMatchResult.kt` |
| Android     | `app/.../data/remote/dto/RecipeDto.kt` |
| Android     | `app/.../data/local/entity/RecipeEntity.kt` |
| Android     | `app/.../data/mapper/RecipeMappers.kt` |
| Android     | `app/.../ui/screens/detail/RecipeDetailViewModel.kt` |
| Android     | `app/.../ui/screens/detail/RecipeDetailScreen.kt` (ingredients block) |
| Android     | `app/.../ui/screens/shopping/ShoppingListScreen.kt` |
| Android     | `app/.../ui/screens/cookwith/CookWithWhatIHaveViewModel.kt` |
| Android     | `app/.../ui/screens/cookwith/CookWithWhatIHaveScreen.kt` |
| Android     | `app/.../ui/screens/edit/EditRecipeViewModel.kt` (ingredientsStructured from lines) |

All of the above are already implemented and consistent in the repository.
