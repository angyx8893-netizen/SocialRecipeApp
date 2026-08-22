import html
import ipaddress
import json
import os
import re
import secrets
import socket
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    import yt_dlp
except Exception:
    yt_dlp = None

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
APP_API_KEY = os.getenv("APP_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()
TRANSCRIBE_MODEL = os.getenv("TRANSCRIBE_MODEL", "gpt-4o-mini-transcribe").strip()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "").strip()
ENABLE_MEDIA_TRANSCRIPTION = os.getenv("ENABLE_MEDIA_TRANSCRIPTION", "true").lower() in {"1", "true", "yes", "on"}
MAX_MEDIA_SECONDS = int(os.getenv("MAX_MEDIA_SECONDS", "1200"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "18"))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "900"))

USER_AGENT = "Mozilla/5.0 (Linux; Android 15) AppleWebKit/537.36 Chrome/132.0 Safari/537.36"
_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}

app = FastAPI(title="SocialRecipeApp Backend", version="3.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class ImportRequest(BaseModel):
    url: str = ""
    raw_text: Optional[str] = None
    platform: Optional[str] = None
    language: str = "it"
    allow_transcription: bool = True


class ImportResponse(BaseModel):
    title: str
    ingredients: str
    procedure: str
    notes: str = ""
    imageUrl: Optional[str] = None
    sourcePlatform: str = "Web / Altro"
    usedAi: bool = False
    extractionMethod: str = "fallback"
    confidence: int = 0
    detectedLanguage: Optional[str] = None
    translated: bool = False
    transcriptionUsed: bool = False
    recipeDetected: bool = False
    warnings: List[str] = Field(default_factory=list)
    servings: Optional[str] = None
    prepTimeMinutes: Optional[int] = None
    cookTimeMinutes: Optional[int] = None
    difficulty: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


def clean(value: Any) -> str:
    if value is None:
        return ""
    text = html.unescape(str(value)).replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def platform_name(url: str, hint: Optional[str]) -> str:
    hay = f"{url} {hint or ''}".lower()
    checks = [
        ("YouTube", ["youtube", "youtu.be"]),
        ("Instagram", ["instagram", "instagr.am"]),
        ("TikTok", ["tiktok"]),
        ("Facebook", ["facebook", "fb.watch", "fb.com"]),
        ("Pinterest", ["pinterest", "pin.it"]),
        ("Threads", ["threads.net"]),
        ("X / Twitter", ["x.com", "twitter.com"]),
        ("Reddit", ["reddit", "redd.it"]),
        ("Telegram", ["t.me", "telegram"]),
    ]
    for name, tokens in checks:
        if any(token in hay for token in tokens):
            return name
    return "Web / Altro"


def public_url(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(400, "URL non valido")
    try:
        infos = socket.getaddrinfo(parsed.hostname, None)
    except OSError:
        raise HTTPException(400, "Host non raggiungibile")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise HTTPException(400, "Sono consentiti solo URL pubblici")
    return value


def safe_get(url: str) -> requests.Response:
    current = public_url(url)
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "it-IT,it;q=0.9,en;q=0.8"}
    for _ in range(6):
        response = requests.get(current, headers=headers, timeout=REQUEST_TIMEOUT, allow_redirects=False)
        if response.status_code not in {301, 302, 303, 307, 308}:
            return response
        location = response.headers.get("location")
        if not location:
            return response
        current = public_url(urljoin(current, location))
    raise requests.TooManyRedirects()


def require_key(candidate: Optional[str]) -> None:
    if APP_API_KEY and (not candidate or not secrets.compare_digest(candidate.strip(), APP_API_KEY)):
        raise HTTPException(401, "Chiave app non valida")


def oembed(url: str, platform: str) -> Dict[str, Any]:
    if not url:
        return {}
    endpoint = None
    if platform == "TikTok":
        endpoint = "https://www.tiktok.com/oembed?url=" + quote(url, safe="")
    elif platform == "YouTube":
        endpoint = "https://www.youtube.com/oembed?format=json&url=" + quote(url, safe="")
    if not endpoint:
        return {}
    try:
        r = safe_get(endpoint)
        return r.json() if r.ok else {}
    except Exception:
        return {}


def generic_metadata(url: str) -> Dict[str, Any]:
    if not url:
        return {}
    try:
        r = safe_get(url)
        if not r.ok:
            return {}
        soup = BeautifulSoup(r.text[:2_000_000], "html.parser")
        def meta(*keys: str) -> str:
            for key in keys:
                tag = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key})
                if tag and tag.get("content"):
                    return clean(tag.get("content"))
            return ""
        data: Dict[str, Any] = {
            "title": meta("og:title", "twitter:title") or clean(soup.title.string if soup.title else ""),
            "description": meta("og:description", "description", "twitter:description"),
            "image": meta("og:image", "twitter:image"),
            "recipe": None,
        }
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            try:
                raw = json.loads(script.string or "{}")
            except Exception:
                continue
            stack = raw if isinstance(raw, list) else [raw]
            for obj in stack:
                graph = obj.get("@graph", []) if isinstance(obj, dict) else []
                candidates = [obj, *graph] if isinstance(obj, dict) else graph
                for item in candidates:
                    typ = item.get("@type", "") if isinstance(item, dict) else ""
                    types = typ if isinstance(typ, list) else [typ]
                    if "Recipe" in types:
                        data["recipe"] = item
                        return data
        return data
    except Exception:
        return {}


def youtube_api(url: str) -> Dict[str, Any]:
    if not YOUTUBE_API_KEY:
        return {}
    match = re.search(r"(?:v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{11})", url)
    if not match:
        return {}
    endpoint = "https://www.googleapis.com/youtube/v3/videos?part=snippet&id=" + match.group(1) + "&key=" + quote(YOUTUBE_API_KEY, safe="")
    try:
        r = safe_get(endpoint)
        items = r.json().get("items", []) if r.ok else []
        if not items:
            return {}
        sn = items[0].get("snippet", {})
        thumbs = sn.get("thumbnails", {})
        image = ""
        for key in ["maxres", "standard", "high", "medium", "default"]:
            if thumbs.get(key, {}).get("url"):
                image = thumbs[key]["url"]
                break
        return {"title": sn.get("title", ""), "description": sn.get("description", ""), "image": image}
    except Exception:
        return {}


def ytdlp_info(url: str) -> Dict[str, Any]:
    if not url or yt_dlp is None:
        return {}
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "skip_download": True, "noplaylist": True, "socket_timeout": REQUEST_TIMEOUT}) as ydl:
            info = ydl.extract_info(url, download=False)
        return info if isinstance(info, dict) else {}
    except Exception:
        return {}


def transcript_from_subtitles(info: Dict[str, Any]) -> str:
    groups = [info.get("subtitles") or {}, info.get("automatic_captions") or {}]
    for group in groups:
        for lang in ["it", "en", "es", "fr", "de"]:
            tracks = group.get(lang) or []
            for track in tracks:
                url = track.get("url")
                if not url:
                    continue
                try:
                    text = safe_get(url).text
                    text = re.sub(r"WEBVTT.*?\n", "", text, flags=re.S)
                    text = re.sub(r"\d\d:\d\d[:.]\d.*?-->.*?\n", "", text)
                    text = re.sub(r"<[^>]+>", "", text)
                    lines = [clean(x) for x in text.splitlines() if clean(x) and not x.strip().isdigit()]
                    return clean(" ".join(dict.fromkeys(lines)))[:24000]
                except Exception:
                    pass
    return ""


def openai_client():
    if not OPENAI_API_KEY or OpenAI is None:
        return None
    try:
        return OpenAI(api_key=OPENAI_API_KEY)
    except Exception:
        return None


def audio_transcript(url: str, duration: Optional[float]) -> str:
    client = openai_client()
    if not ENABLE_MEDIA_TRANSCRIPTION or client is None or yt_dlp is None:
        return ""
    if duration and duration > MAX_MEDIA_SECONDS:
        return ""
    try:
        with tempfile.TemporaryDirectory(prefix="socialrecipe_") as tmp:
            outtmpl = str(Path(tmp) / "audio.%(ext)s")
            opts = {
                "quiet": True, "no_warnings": True, "noplaylist": True,
                "format": "bestaudio[filesize<24M]/bestaudio[filesize_approx<24M]/bestaudio/best",
                "outtmpl": outtmpl, "socket_timeout": REQUEST_TIMEOUT, "max_filesize": 24 * 1024 * 1024,
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.extract_info(url, download=True)
            files = [p for p in Path(tmp).iterdir() if p.is_file() and p.stat().st_size < 24 * 1024 * 1024]
            if not files:
                return ""
            audio = max(files, key=lambda p: p.stat().st_size)
            with audio.open("rb") as handle:
                result = client.audio.transcriptions.create(
                    model=TRANSCRIBE_MODEL,
                    file=handle,
                    prompt="Video di cucina: conserva esattamente ingredienti, quantità, tempi e temperature.",
                )
            return clean(getattr(result, "text", ""))[:24000]
    except Exception:
        return ""


def source_bundle(payload: ImportRequest) -> Tuple[Dict[str, Any], List[str], bool]:
    url = public_url(payload.url) if payload.url.strip() else ""
    platform = platform_name(url, payload.platform)
    methods: List[str] = []
    warnings: List[str] = []
    title = ""
    description = clean(payload.raw_text or "")
    image = ""
    transcript = ""
    recipe: Optional[Dict[str, Any]] = None
    if description:
        methods.append("testo condiviso")

    oe = oembed(url, platform)
    if oe:
        title = clean(oe.get("title"))
        description = description or clean(oe.get("title"))
        image = clean(oe.get("thumbnail_url"))
        methods.append("oEmbed")

    if platform == "YouTube":
        yt = youtube_api(url)
        if yt:
            title = title or clean(yt.get("title"))
            description = description or clean(yt.get("description"))
            image = image or clean(yt.get("image"))
            methods.append("YouTube API")

    page = generic_metadata(url)
    if page:
        title = title or clean(page.get("title"))
        description = description or clean(page.get("description"))
        image = image or clean(page.get("image"))
        recipe = page.get("recipe")
        methods.append("metadata pagina")
        if recipe:
            methods.append("JSON-LD Recipe")

    media = ytdlp_info(url)
    if media:
        title = title or clean(media.get("title"))
        description = description or clean(media.get("description"))
        image = image or clean(media.get("thumbnail"))
        transcript = transcript_from_subtitles(media)
        if transcript:
            methods.append("sottotitoli")
        methods.append("yt-dlp")

    transcription_used = False
    combined = clean(description + "\n" + transcript)
    if payload.allow_transcription and url and len(combined) < 180:
        audio = audio_transcript(url, media.get("duration") if media else None)
        if audio:
            transcript = clean(transcript + "\n" + audio)
            transcription_used = True
            methods.append("trascrizione audio")

    return {
        "url": url, "platform": platform, "title": title, "description": description,
        "transcript": transcript, "image": image, "recipe": recipe, "methods": methods,
    }, warnings, transcription_used


def direct_recipe(bundle: Dict[str, Any]) -> Optional[ImportResponse]:
    recipe = bundle.get("recipe")
    if not isinstance(recipe, dict):
        return None
    ingredients = recipe.get("recipeIngredient") or []
    instructions = recipe.get("recipeInstructions") or []
    if isinstance(instructions, list):
        steps = []
        for item in instructions:
            steps.append(clean(item.get("text", "")) if isinstance(item, dict) else clean(item))
    else:
        steps = [clean(instructions)]
    ingredients = [clean(x) for x in ingredients if clean(x)]
    steps = [x for x in steps if x]
    if not ingredients and not steps:
        return None
    return ImportResponse(
        title=clean(recipe.get("name")) or bundle.get("title") or "Ricetta importata",
        ingredients="\n".join(f"- {x}" for x in ingredients),
        procedure="\n".join(f"{i+1}. {x}" for i, x in enumerate(steps)),
        notes="Ricetta ricavata dai dati strutturati della pagina.",
        imageUrl=bundle.get("image"), sourcePlatform=bundle.get("platform", "Web / Altro"),
        usedAi=False, extractionMethod=" + ".join(bundle.get("methods") or ["JSON-LD"]),
        confidence=90, translated=False, transcriptionUsed=False, recipeDetected=True,
        servings=clean(recipe.get("recipeYield")) or None,
    )


def ai_extract(bundle: Dict[str, Any], warnings: List[str], transcription_used: bool, language: str) -> Optional[ImportResponse]:
    client = openai_client()
    if client is None:
        return None
    source = clean("\n\n".join([bundle.get("description", ""), bundle.get("transcript", "")]))[:24000]
    if not source:
        return None
    prompt = f"""Estrai una ricetta dal contenuto seguente e restituisci SOLO JSON valido.
Lingua finale: italiano. Traduci in modo culinario naturale, ma NON inventare ingredienti, quantità, tempi o temperature mancanti.
Se una quantità non è presente, lascia l'ingrediente senza quantità. Mantieni unità e numeri esatti.
Campi JSON obbligatori: title, ingredients, procedure, notes, recipeDetected, confidence, detectedLanguage, translated, servings, prepTimeMinutes, cookTimeMinutes, difficulty, tags, warnings.
ingredients e procedure devono essere stringhe multilinea; confidence 0-100; tags e warnings array.
Piattaforma: {bundle.get('platform')}
Titolo: {bundle.get('title')}
Fonte: {bundle.get('url')}
CONTENUTO:\n{source}"""
    try:
        result = client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "Sei un estrattore di ricette rigoroso. Non inventare dati."},
                {"role": "user", "content": prompt},
            ],
        )
        data = json.loads(result.choices[0].message.content or "{}")
        ai_warnings = [clean(x) for x in data.get("warnings", []) if clean(x)]
        return ImportResponse(
            title=clean(data.get("title")) or bundle.get("title") or "Ricetta importata",
            ingredients=clean(data.get("ingredients")), procedure=clean(data.get("procedure")),
            notes=clean(data.get("notes")), imageUrl=bundle.get("image"), sourcePlatform=bundle.get("platform", "Web / Altro"),
            usedAi=True, extractionMethod=" + ".join(dict.fromkeys(bundle.get("methods") or ["AI"])),
            confidence=max(0, min(100, int(data.get("confidence", 0) or 0))),
            detectedLanguage=clean(data.get("detectedLanguage")) or None, translated=bool(data.get("translated", False)),
            transcriptionUsed=transcription_used, recipeDetected=bool(data.get("recipeDetected", False)),
            warnings=list(dict.fromkeys([*warnings, *ai_warnings])), servings=clean(data.get("servings")) or None,
            prepTimeMinutes=int(data.get("prepTimeMinutes", 0) or 0) or None,
            cookTimeMinutes=int(data.get("cookTimeMinutes", 0) or 0) or None,
            difficulty=clean(data.get("difficulty")) or None,
            tags=[clean(x) for x in data.get("tags", []) if clean(x)][:8],
        )
    except Exception as exc:
        warnings.append("AI temporaneamente non disponibile: " + clean(exc)[:120])
        return None


def heuristic(bundle: Dict[str, Any], warnings: List[str], transcription_used: bool) -> ImportResponse:
    text = clean(bundle.get("description", "") + "\n" + bundle.get("transcript", ""))
    lines = [clean(x).strip("-• ") for x in re.split(r"\n|•|;", text) if clean(x)]
    qty = re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:g|kg|ml|cl|l|cup|cups|tbsp|tsp|cucchiai?|cucchiaini?)\b", re.I)
    actions = re.compile(r"\b(aggiungi|mescola|cuoci|inforna|versa|taglia|frulla|rosola|servi|add|mix|cook|bake|stir|chop)\b", re.I)
    ingredients = list(dict.fromkeys([x for x in lines if qty.search(x)]))[:30]
    steps = list(dict.fromkeys([x for x in lines if actions.search(x)]))[:20]
    if openai_client() is None:
        warnings.append("OpenAI non configurata sul backend cloud.")
    if not ingredients:
        warnings.append("Ingredienti non ricavati con sufficiente affidabilità.")
    if not steps:
        warnings.append("Procedimento non ricavato con sufficiente affidabilità.")
    detected = bool(ingredients or steps)
    return ImportResponse(
        title=bundle.get("title") or f"Ricetta da {bundle.get('platform', 'social')}",
        ingredients="\n".join(f"- {x}" for x in ingredients),
        procedure="\n".join(f"{i+1}. {x}" for i, x in enumerate(steps)),
        notes="Estrazione prudente senza invenzioni: verifica eventuali campi mancanti.",
        imageUrl=bundle.get("image"), sourcePlatform=bundle.get("platform", "Web / Altro"),
        usedAi=False, extractionMethod=" + ".join(dict.fromkeys(bundle.get("methods") or ["fallback"])),
        confidence=45 if detected else 10, translated=False, transcriptionUsed=transcription_used,
        recipeDetected=detected, warnings=list(dict.fromkeys(warnings)),
    )


def cache_key(payload: ImportRequest) -> str:
    return json.dumps(payload.model_dump(), sort_keys=True, ensure_ascii=False)


def process(payload: ImportRequest) -> ImportResponse:
    if not payload.url.strip() and not clean(payload.raw_text):
        raise HTTPException(400, "Serve almeno un URL o il testo condiviso")
    key = cache_key(payload)
    cached = _CACHE.get(key)
    if cached and time.time() - cached[0] <= CACHE_TTL_SECONDS:
        result = ImportResponse.model_validate(cached[1])
        result.extractionMethod += " + cache"
        return result
    bundle, warnings, transcription_used = source_bundle(payload)
    result = direct_recipe(bundle)
    if result is None or openai_client() is not None:
        result = ai_extract(bundle, warnings, transcription_used, payload.language) or result
    if result is None:
        result = heuristic(bundle, warnings, transcription_used)
    _CACHE[key] = (time.time(), result.model_dump())
    if len(_CACHE) > 128:
        oldest = min(_CACHE, key=lambda k: _CACHE[k][0])
        _CACHE.pop(oldest, None)
    return result


@app.get("/")
def root():
    return {"status": "ok", "service": "SocialRecipeApp Backend", "version": "3.1.0", "docs": "/docs"}


@app.get("/health")
def health():
    return {
        "ok": True, "version": "3.1.0",
        "openaiConfigured": bool(OPENAI_API_KEY and OpenAI is not None),
        "youtubeApiConfigured": bool(YOUTUBE_API_KEY),
        "model": OPENAI_MODEL, "transcribeModel": TRANSCRIBE_MODEL,
        "mediaTranscriptionEnabled": ENABLE_MEDIA_TRANSCRIPTION,
        "ytdlpAvailable": yt_dlp is not None, "authConfigured": bool(APP_API_KEY),
        "cacheEnabled": CACHE_TTL_SECONDS > 0,
        "hosting": "render" if os.getenv("RENDER") else "local",
    }


@app.get("/health/auth")
def health_auth(x_app_key: Optional[str] = Header(default=None, alias="X-App-Key")):
    require_key(x_app_key)
    return health()


@app.post("/extract-recipe", response_model=ImportResponse)
def extract_recipe(payload: ImportRequest, x_app_key: Optional[str] = Header(default=None, alias="X-App-Key")):
    require_key(x_app_key)
    return process(payload)


@app.post("/api/v1/import", response_model=ImportResponse)
def api_v1_import(payload: ImportRequest, x_app_key: Optional[str] = Header(default=None, alias="X-App-Key")):
    require_key(x_app_key)
    return process(payload)
