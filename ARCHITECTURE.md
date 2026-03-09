# SocialRecipeApp – Architecture

## Overview

- **Android**: Kotlin, Jetpack Compose, Material 3, MVVM, Room, Retrofit, Hilt.
- **Backend**: Python FastAPI, Pydantic, modular routers/services.

## Package Structure (Android)

```
app/
  di/                    # Hilt modules
  SocialRecipeApp.kt     # Application class
  navigation/            # NavGraph, routes
  ui/
    screens/             # Screen composables + ViewModels
    components/          # Reusable UI components
    theme/               # Color, Type, Theme
  data/
    local/               # Room DAO, Database, Entity
    remote/              # Retrofit API, DTOs
    repository/          # RecipeRepository, ShoppingRepository, etc.
    mapper/              # DTO <-> Domain model mappers
  domain/
    model/               # Recipe, Ingredient, ShoppingItem, etc.
    repository/          # Repository interfaces
    usecase/             # Use cases (optional; logic in VM/Repo)
```

## Data Flow

1. User shares/pastes URL → Import screen.
2. App validates URL → POST /import-recipe (or /normalize-recipe).
3. Backend: validate URL, detect platform, extract text, detect language, translate if needed, normalize recipe.
4. Backend returns standardized recipe JSON.
5. App maps to domain model, saves in Room, navigates to detail or archive.
6. Archive/detail/favorites read from Room (offline-first).

## API Contracts (Backend)

- `GET /health` → `{ "status": "ok" }`
- `POST /import-recipe` → body: `{ "url": "string" }` → returns full normalized recipe.
- `POST /normalize-recipe` → body: raw text or partial recipe → returns normalized recipe.
- `POST /translate-recipe` → body: recipe + target_lang → returns translated fields.
- `POST /detect-language` → body: `{ "text": "string" }` → returns `{ "language": "it", "confidence": 0.9 }`.

## Room Entities

- **Recipe**: id, sourceUrl, sourcePlatform, author, title, coverImage, originalLanguage, translatedLanguage, ingredientsRaw, ingredientsStructured (JSON), steps (JSON), notes, servings, prepTimeMinutes, cookTimeMinutes, tags (JSON), category, importedAt, isFavorite.
- **ShoppingItem**: id, name, quantity, unit, recipeId?, checked, addedAt.

## Navigation Routes

- splash, home, import_link, import_loading, archive, recipe_detail/{id}, favorites, edit_recipe/{id}, shopping_list, cook_with_what_i_have, settings.

## Domain Models (Android)

- Recipe, IngredientStructured, Step, ShoppingItem, ImportState, ThemeMode, Settings.
