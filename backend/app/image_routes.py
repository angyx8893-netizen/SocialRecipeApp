import base64
import binascii
import json
from typing import Any, Callable, Dict, Optional, Type

from fastapi import Header, HTTPException
from pydantic import BaseModel, Field

MAX_IMAGE_BYTES = 6 * 1024 * 1024


class ImageImportRequest(BaseModel):
    image_base64: str = Field(description="Immagine JPEG/PNG/WebP codificata Base64")
    mime_type: str = "image/jpeg"
    platform: str = "Screenshot / Foto"
    language: str = "it"


def _decode(payload: ImageImportRequest) -> tuple[str, str]:
    mime = (payload.mime_type or "image/jpeg").strip().lower()
    if mime not in {"image/jpeg", "image/jpg", "image/png", "image/webp"}:
        raise HTTPException(400, "Formato immagine non supportato. Usa JPG, PNG o WebP.")
    raw = (payload.image_base64 or "").strip()
    if raw.startswith("data:"):
        _, _, raw = raw.partition(",")
    if not raw:
        raise HTTPException(400, "Immagine mancante.")
    try:
        decoded = base64.b64decode(raw, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(400, "Immagine Base64 non valida.")
    if not decoded:
        raise HTTPException(400, "Immagine vuota.")
    if len(decoded) > MAX_IMAGE_BYTES:
        raise HTTPException(413, "Immagine troppo grande. Limite 6 MB.")
    return mime, base64.b64encode(decoded).decode("ascii")


def _schema() -> Dict[str, Any]:
    return {
        "name": "social_recipe_image_extraction",
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "sourceText": {"type": "string"},
                "title": {"type": "string"},
                "ingredients": {"type": "string"},
                "procedure": {"type": "string"},
                "notes": {"type": "string"},
                "recipeDetected": {"type": "boolean"},
                "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
                "detectedLanguage": {"type": "string"},
                "translated": {"type": "boolean"},
                "servings": {"type": "string"},
                "prepTimeMinutes": {"type": "integer", "minimum": 0},
                "cookTimeMinutes": {"type": "integer", "minimum": 0},
                "difficulty": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
                "warnings": {"type": "array", "items": {"type": "string"}, "maxItems": 8}
            },
            "required": [
                "sourceText", "title", "ingredients", "procedure", "notes", "recipeDetected",
                "confidence", "detectedLanguage", "translated", "servings", "prepTimeMinutes",
                "cookTimeMinutes", "difficulty", "tags", "warnings"
            ]
        },
        "strict": True
    }


def register_image_routes(
    app,
    ImportResponse: Type[BaseModel],
    openai_client: Callable[[], Any],
    require_key: Callable[[Optional[str]], None],
    model: str,
    clean: Callable[[Any], str]
) -> None:
    @app.post("/api/v1/import-image", response_model=ImportResponse)
    def import_image(payload: ImageImportRequest, x_app_key: Optional[str] = Header(default=None, alias="X-App-Key")):
        require_key(x_app_key)
        client = openai_client()
        if client is None:
            raise HTTPException(503, "OpenAI non configurata sul backend cloud.")

        mime, normalized = _decode(payload)
        data_url = f"data:{mime};base64,{normalized}"
        prompt = """
Analizza questa foto o screenshot di un post social e ricava la ricetta visibile.
Lingua finale richiesta: italiano.

REGOLE:
1. sourceText deve contenere la trascrizione fedele del testo utile del post/didascalia/ricetta visibile nell'immagine.
2. Ignora elementi dell'interfaccia come ora, batteria, pulsanti, barra commenti e menu, salvo il nome autore se utile.
3. Non inventare testo non leggibile e non completare quantità mancanti.
4. title = titolo della ricetta, tradotto in italiano solo se necessario.
5. ingredients = una riga per ingrediente con prefisso '- '. Conserva quantità esattamente come visibili.
6. procedure = passaggi numerati e ordinati. Non aggiungere passaggi plausibili ma assenti.
7. Se il testo è in italiano, translated=false.
8. recipeDetected=false se non è realmente presente una ricetta leggibile.
9. confidence 0-100 misura quanto i dati sono leggibili e supportati dall'immagine.
10. servings, tempi e difficulty solo se esplicitamente presenti; altrimenti stringa vuota/0.
11. warnings segnala solo parti illeggibili o ambigue realmente rilevanti.
""".strip()

        try:
            response = client.chat.completions.create(
                model=model,
                temperature=0.0,
                messages=[
                    {"role": "system", "content": "Sei un estrattore visivo di ricette rigoroso. Trascrivi fedelmente e non inventare dati."},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": data_url, "detail": "high"}}
                        ]
                    }
                ],
                response_format={"type": "json_schema", "json_schema": _schema()}
            )
            content = response.choices[0].message.content
            if not content:
                raise HTTPException(502, "L'AI non ha restituito testo dall'immagine.")
            data = json.loads(content)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(502, "Analisi immagine non riuscita: " + clean(str(exc))[:180])

        warnings = [clean(x) for x in data.get("warnings", []) if clean(x)]
        source_text = clean(data.get("sourceText", ""))[:24000]
        return ImportResponse(
            title=clean(data.get("title", "")) or "Ricetta da screenshot",
            ingredients=clean(data.get("ingredients", "")),
            procedure=clean(data.get("procedure", "")),
            notes=clean(data.get("notes", "")),
            sourceText=source_text,
            imageUrl=None,
            sourcePlatform=clean(payload.platform) or "Screenshot / Foto",
            usedAi=True,
            extractionMethod="AI Vision da foto/screenshot",
            confidence=max(0, min(100, int(data.get("confidence", 0) or 0))),
            detectedLanguage=clean(data.get("detectedLanguage", "")) or None,
            translated=bool(data.get("translated", False)),
            transcriptionUsed=False,
            recipeDetected=bool(data.get("recipeDetected", False)),
            warnings=warnings,
            servings=clean(data.get("servings", "")) or None,
            prepTimeMinutes=int(data.get("prepTimeMinutes", 0) or 0) or None,
            cookTimeMinutes=int(data.get("cookTimeMinutes", 0) or 0) or None,
            difficulty=clean(data.get("difficulty", "")) or None,
            tags=[clean(x) for x in data.get("tags", []) if clean(x)][:8]
        )
