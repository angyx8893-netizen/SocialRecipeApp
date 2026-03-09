# Final consistency audit

## Backend parsing consistency
- **text_parser.py**: Section split (ingredients_section / steps_section), parse_ingredient_line → quantity, unit, name, original_text. No ingredient lines in steps; cooking-verb fallback when no procedure section.
- **extraction_service.py**: Uses extract_recipe_sections; returns ingredients_raw, ingredients_structured, steps. No placeholder recipes; empty lists when no recipe.
- **schemas/recipe.py**: IngredientStructuredSchema(quantity, unit, name, original_text); RecipeResponse has ingredients_raw, ingredients_structured, steps (snake_case for API).

## Android model consistency
- **Recipe**: ingredientsRaw, ingredientsStructured (List<IngredientStructured>).
- **IngredientStructured**: quantity, unit, name, originalText (nullable).
- **RecipeMatchResult**: recipe, matchPercentage, matchedIngredients, missingIngredients.
- **ShoppingItem**: id, name, quantity, unit, recipeId, checked, addedAt.

## Room entity/model consistency
- **RecipeEntity**: ingredientsRawJson, ingredientsStructuredJson (Gson serializes List<String> and List<IngredientStructuredDto>).
- **ShoppingItemEntity**: name, quantity, unit, recipeId, checked, addedAt.
- **RecipeMappers**: RecipeDto ↔ Recipe (toDomain/toEntity); IngredientStructuredDto ↔ IngredientStructured (originalText ↔ original_text).
- **ShoppingMappers**: ShoppingItemEntity ↔ ShoppingItem.
- **parseIngredientList**: Handles blank JSON and DTOs with null originalText (old data).

## API response/model consistency
- Backend **RecipeResponse** (snake_case): ingredients_raw, ingredients_structured (list of {quantity, unit, name, original_text}), steps.
- Android **RecipeDto**: @SerializedName("ingredients_raw"), @SerializedName("ingredients_structured"); IngredientStructuredDto has @SerializedName("original_text") originalText.
- **translate-recipe** endpoint: Builds IngredientStructuredSchema with quantity, unit, name, **original_text** (fixed in audit).

## Shopping list compatibility
- **RecipeDetailViewModel.addAllToShoppingList()**: Uses recipe.ingredientsStructured; display name = originalText ?: quantity+unit+name; passes quantity, unit to ShoppingItem. Fallback: if ingredientsStructured.isEmpty(), uses ingredientsRaw (single fallback).
- **ShoppingListScreen**: Shows items with quantity, unit, name from ShoppingItem.
- **ShoppingItem** / **ShoppingItemEntity**: Store name, quantity, unit; no schema change.

## Cook-with-what-I-have compatibility
- **CookWithWhatIHaveViewModel**: Uses recipeRepository.getAllRecipes() (saved only). Match on recipe.ingredientsStructured (ing.name) or fallback ingredientsRaw. Normalize (lowercase, trim, filler words, base form for plural). Single fallback: ingredientsStructured if non-empty else raw.
- **RecipeMatchResult**: recipe, matchPercentage, matchedIngredients, missingIngredients.
- **CookWithWhatIHaveScreen**: Multiline input, match cards, onRecipeClick → detail. No fake data.

## Duplicate fallback logic
- **Single fallback** in add-to-shopping: ingredientsStructured first, then ingredientsRaw.
- **Single fallback** in cook-with: ingredientsStructured first, then ingredientsRaw for building list. No duplicate branches.

## Placeholder recipes
- **Backend**: No placeholder; extraction_service returns empty ingredients/steps when nothing parsed. Comments state "no placeholder".
- **Android**: No hardcoded fake recipes; Cook-with shows only recipes with ≥1 match from saved data.

## Imports and compile
- All referenced ViewModels, Screens, DTOs, entities, mappers, and NavGraph routes verified. No broken imports or missing types.
- Lint run on modified and key files: no errors.

## Fix applied during audit
- **backend/app/routers/recipe.py**: translate_recipe endpoint now builds IngredientStructuredSchema with **original_text** and uses string defaults (quantity/unit "") for consistency with schema and Android.
