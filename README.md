# SocialRecipeApp

A production-style Android app that lets you save recipes from social media by sharing or pasting links. The app sends the URL to a FastAPI backend for validation, platform detection, text extraction, language detection, translation to Italian when needed, and normalization into a structured recipe. Recipes are stored locally for offline use.

---

## Project overview

- **Android app**: Kotlin, Jetpack Compose, Material 3, MVVM, Room, Retrofit, Hilt. Clean architecture with `domain` / `data` / `ui` layers.
- **Backend**: Python FastAPI, Pydantic, modular `routers` / `services` / `schemas` / `utils`.

Supported sources (architecture-ready; extraction is demo-safe and extensible):

- Instagram, TikTok, Facebook, YouTube Shorts, generic public links.

---

## Android setup

### Requirements

- Android Studio Ladybug (2024.2.1) or newer (or compatible)
- JDK 17
- Android SDK 34, minSdk 26

### Steps

1. Open the project in Android Studio: **File → Open** → select the `SocialRecipeApp` folder (the one containing `build.gradle.kts` and `app/`).
2. Sync Gradle and wait for dependencies to resolve.
3. Use an emulator or a physical device with USB debugging. For the emulator, use a device with API 26+ (e.g. Pixel 6 API 34).

### Run the app

1. Select a device/emulator.
2. Run **Run → Run 'app'** (or the Run button).
3. The app starts on the **Splash** screen, then **Home**. From Home you can open **Import**, **Archive**, **Favorites**, **Shopping list**, **Cook with what I have**, and **Settings**.

### Share intent

- From another app (browser, Instagram, etc.), use **Share** and choose **Social Recipe**. The shared URL is opened in the import flow.
- You can also open the app and paste a link on the **Import** screen.

---

## Backend setup

### Requirements

- Python 3.9+

### Steps

1. Open a terminal in the project root (parent of `SocialRecipeApp` and `backend`).
2. Create and activate a virtual environment:

   ```bash
   cd SocialRecipeApp/backend
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the server:

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   API base URL: `http://localhost:8000` (on the host). From the Android emulator use `http://10.0.2.2:8000` (default in app settings).

### Endpoints

- `GET /health` – health check.
- `POST /import-recipe` – body: `{ "url": "https://..." }`. Returns normalized recipe JSON.
- `POST /normalize-recipe` – body: `{ "url", "text", "source_platform" }`. Normalizes given text/URL into a recipe.
- `POST /detect-language` – body: `{ "text": "..." }`. Returns `{ "language", "confidence" }`.
- `POST /translate-recipe` – body: recipe object + `target_language`. Placeholder; returns recipe (optionally translated when implemented).

---

## Local run summary

1. **Backend**: From `backend/`, run `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`.
2. **Android**: In Android Studio, run the app on an emulator or device. In **Settings**, set **Backend URL** to `http://10.0.2.2:8000` for the default emulator (or your machine’s IP if using a physical device on the same network).

---

## Emulator / device notes

- **Emulator**: Use `http://10.0.2.2:8000` as the backend URL so the app can reach the host’s `localhost:8000`.
- **Physical device**: Use your computer’s LAN IP (e.g. `http://192.168.1.10:8000`) and ensure the device and PC are on the same network and that the firewall allows port 8000.

---

## Import flow

1. User shares a URL into the app or pastes it on the Import screen.
2. App validates the URL and navigates to the import-loading screen.
3. App sends `POST /import-recipe` with the URL.
4. Backend validates the URL, detects platform, runs demo-safe extraction (placeholder text if no real scraper), detects language, translates to Italian if needed, and normalizes to a standard recipe schema.
5. Backend returns the recipe JSON.
6. App maps the response to the domain model, saves the recipe in Room (duplicate by `source_url` is handled via replace), and shows success or error.
7. User can open the recipe in detail, edit it, add ingredients to the shopping list, or mark as favorite.

---

## Known limitations

- **Extraction**: No real scraping of Instagram/TikTok/Facebook/YouTube. The backend uses a demo-safe path (placeholder text and generic parsing). The structure is ready for real adapters or third-party APIs.
- **Translation**: Uses `googletrans`; rate limits or network issues may affect translation. Can be replaced with a paid API for production.
- **Backend URL**: Changing the backend URL in Settings takes effect for new requests; the app may need a restart to recreate the Retrofit client with the new base URL in some setups.

---

## Future extension ideas

- Real platform adapters (e.g. official or permitted APIs) for Instagram, TikTok, etc.
- Optional ingredient parsing (quantity/unit/name) and auto-tags (vegetarian, quick, oven, etc.).
- Duplicate detection by `source_url` (already supported in DB); optional import history log.
- Richer empty and error states, and optional import history screen.
- Backup/restore or sync (e.g. with a cloud backend).

---

## Layout (high level)

```
SocialRecipeApp/          # Android project
  app/
    src/main/java/com/socialrecipeapp/
      di/                 # Hilt modules
      navigation/         # NavGraph, Routes
      ui/screens/         # Compose screens + ViewModels
      ui/theme/           # Colors, Typography, Theme
      ui/components/      # RecipeCard, etc.
      data/local/         # Room DAO, Database, Entities
      data/remote/        # Retrofit API, DTOs
      data/repository/    # Repository implementations
      data/mapper/        # DTO/Entity ↔ domain mappers
      domain/model/       # Recipe, ShoppingItem, etc.
      domain/repository/ # Repository interfaces
  build.gradle.kts, settings.gradle.kts, app/build.gradle.kts

backend/                  # FastAPI
  app/
    main.py
    routers/              # health, recipe
    services/              # extraction_service
    schemas/               # recipe (Pydantic)
    utils/                 # url_parser, text_parser, language
  requirements.txt
```

---

## License

This project is for educational and portfolio use. Ensure compliance with platform ToS when adding real scraping or third-party APIs.
