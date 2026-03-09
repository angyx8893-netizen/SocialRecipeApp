# API contract (Android ↔ Backend)

Endpoints and JSON shapes are aligned with the Android app (`RecipeApi` and DTOs).

## Base URL

- Local: `http://localhost:8000`
- From Android emulator: `http://10.0.2.2:8000`

## Endpoints

### GET /health

**Response:** `{ "status": "ok" }`

---

### POST /import-recipe

**Request:** `{ "url": "https://..." }`  
**Response:** `RecipeResponse` (see below)

Validates URL, detects platform, extracts content (demo-safe), normalizes and optionally translates to Italian.

---

### POST /normalize-recipe

**Request:** `{ "url": "...", "text": "...", "source_platform": "generic", "title": "..." }` (all optional except at least `text` or `title`)  
**Response:** `RecipeResponse`

Normalizes raw text into a structured recipe.

---

### POST /detect-language

**Request:** `{ "text": "..." }`  
**Response:** `{ "language": "en", "confidence": 0.9 }`

---

### POST /translate-recipe

**Request:** `{ "recipe": { ... }, "target_language": "it" }`  
**Response:** `RecipeResponse`

Returns the recipe (optionally with translated fields when translation is implemented).

---

## RecipeResponse (snake_case for Android)

Same shape as Android `RecipeDto`:

- `id`, `source_url`, `source_platform`, `author`, `title`, `cover_image`
- `original_language`, `translated_language`
- `ingredients_raw` (list of strings)
- `ingredients_structured` (list of `{ "quantity", "unit", "name" }`)
- `steps`, `notes`, `servings`, `prep_time_minutes`, `cook_time_minutes`
- `tags`, `category`, `imported_at`, `is_favorite`
