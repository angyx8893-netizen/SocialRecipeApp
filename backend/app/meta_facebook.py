from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

META_APP_ID = os.getenv("META_APP_ID", "").strip()
META_APP_SECRET = os.getenv("META_APP_SECRET", "").strip()
META_GRAPH_VERSION = os.getenv("META_GRAPH_VERSION", "v25.0").strip() or "v25.0"


def configured() -> bool:
    # Dal 2026 gli endpoint Meta oEmbed per contenuti pubblici possono essere usati
    # senza token. Le credenziali restano solo come fallback opzionale.
    return True


def credentials_configured() -> bool:
    return bool(META_APP_ID and META_APP_SECRET)


def _is_facebook_url(value: str) -> bool:
    try:
        host = (urlparse(value).hostname or "").lower()
    except Exception:
        return False
    return host == "facebook.com" or host.endswith(".facebook.com") or host in {"fb.com", "www.fb.com"}


def _login_target(value: str) -> Optional[str]:
    try:
        parsed = urlparse(value)
        if not _is_facebook_url(value) or "/login" not in parsed.path.lower():
            return None
        values = parse_qs(parsed.query).get("next") or []
        if not values:
            return None
        target = unquote(values[0]).strip()
        return target if _is_facebook_url(target) else None
    except Exception:
        return None


def _canonical_from_story(value: str) -> Optional[str]:
    """Converte story.php?story_fbid=...&id=... nel formato supportato da oEmbed."""
    try:
        parsed = urlparse(value)
        if not _is_facebook_url(value):
            return None
        query = parse_qs(parsed.query)
        story = (query.get("story_fbid") or [""])[0].strip()
        owner = (query.get("id") or [""])[0].strip()
        if story and owner:
            return f"https://www.facebook.com/{owner}/posts/{story}"
    except Exception:
        pass
    return None


def _candidate_urls(url: str) -> List[str]:
    out: List[str] = [url]

    direct = _login_target(url)
    if direct:
        out.append(direct)

    try:
        response = requests.get(
            url,
            timeout=12,
            allow_redirects=False,
            headers={"User-Agent": "facebookexternalhit/1.1"},
        )
        location = response.headers.get("location")
        if location:
            absolute = urljoin(url, location)
            out.append(absolute)
            target = _login_target(absolute)
            if target:
                out.append(target)
    except Exception:
        pass

    expanded: List[str] = []
    for candidate in out:
        if not candidate or not _is_facebook_url(candidate):
            continue
        expanded.append(candidate)
        canonical = _canonical_from_story(candidate)
        if canonical:
            expanded.append(canonical)

        try:
            parsed = urlparse(candidate)
            # Normalizza m./mbasic./fb.com verso www.facebook.com per oEmbed.
            normalized = parsed._replace(netloc="www.facebook.com").geturl()
            expanded.append(normalized)
            canonical = _canonical_from_story(normalized)
            if canonical:
                expanded.append(canonical)
        except Exception:
            pass

    return list(dict.fromkeys(x for x in expanded if x))


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).replace("\r", " ").replace("\n", " ").split()).strip()


def _visible_from_markup(markup: str) -> str:
    if not markup:
        return ""
    soup = BeautifulSoup(markup, "html.parser")
    for script in soup.find_all("script"):
        script.decompose()
    return _clean(soup.get_text("\n", strip=True))[:24000]


def _oembed_request(endpoint: str, candidate: str, with_credentials: bool) -> tuple[Optional[requests.Response], Dict[str, Any]]:
    params: Dict[str, Any] = {
        "url": candidate,
        "omitscript": "true",
        "maxwidth": 658,
    }
    if with_credentials and credentials_configured():
        params["access_token"] = f"{META_APP_ID}|{META_APP_SECRET}"

    try:
        response = requests.get(
            endpoint,
            params=params,
            headers={"Accept": "application/json", "User-Agent": "SocialRecipeApp/3.6"},
            timeout=18,
        )
        data = response.json() if response.content else {}
        return response, data if isinstance(data, dict) else {}
    except Exception as exc:
        return None, {"error_message": _clean(exc)[:240]}


def fetch_post(url: str) -> Dict[str, Any]:
    if not url or not _is_facebook_url(url):
        return {}

    endpoint = f"https://graph.facebook.com/{META_GRAPH_VERSION}/oembed_post"
    last_error: Dict[str, Any] = {}

    for candidate in _candidate_urls(url):
        # 1) Percorso ufficiale tokenless per contenuti pubblici.
        attempts = [False]
        # 2) Fallback con App token solo se l'utente lo ha configurato.
        if credentials_configured():
            attempts.append(True)

        for with_credentials in attempts:
            response, data = _oembed_request(endpoint, candidate, with_credentials)
            if response is None:
                last_error = data
                continue

            if not response.ok:
                error = data.get("error") if isinstance(data, dict) else None
                if isinstance(error, dict):
                    last_error = {
                        "error_code": error.get("code"),
                        "error_message": _clean(error.get("message"))[:240],
                        "candidate_url": candidate,
                    }
                else:
                    last_error = {
                        "error_code": response.status_code,
                        "candidate_url": candidate,
                    }
                continue

            markup = str(data.get("html") or "") if isinstance(data, dict) else ""
            visible = _visible_from_markup(markup)
            return {
                "candidate_url": candidate,
                "author": _clean(data.get("author_name")) if isinstance(data, dict) else "",
                "description": visible,
                "html": markup,
                "tokenless": not with_credentials,
            }

    return last_error


def patch_legacy(legacy) -> None:
    original_source_bundle = legacy.source_bundle

    def source_bundle_with_meta(payload):
        bundle, warnings, transcription_used = original_source_bundle(payload)
        url = bundle.get("url", "")
        platform = bundle.get("platform", "")
        if platform != "Facebook" or not url:
            return bundle, warnings, transcription_used

        meta = fetch_post(url)
        if meta.get("description"):
            description = legacy.clean(meta.get("description", ""))
            existing = legacy.clean(bundle.get("description", ""))
            if description and description not in existing:
                bundle["description"] = legacy.clean("\n".join(x for x in [existing, description] if x))
            bundle["title"] = bundle.get("title") or meta.get("author", "")
            methods = list(bundle.get("methods") or [])
            label = "Meta oEmbed ufficiale tokenless" if meta.get("tokenless") else "Meta oEmbed ufficiale"
            if label not in methods:
                methods.insert(0, label)
            bundle["methods"] = methods
        elif not legacy.clean(bundle.get("description", "")):
            warnings.append(
                "Facebook non ha reso disponibile il contenuto del post tramite oEmbed. "
                "Verifica che il post sia pubblico; se resta bloccato usa lo screenshot mantenendo il link originale."
            )

        return bundle, list(dict.fromkeys(warnings)), transcription_used

    legacy.source_bundle = source_bundle_with_meta

    @legacy.app.get("/meta/status")
    def meta_status():
        return {
            "configured": True,
            "tokenless": True,
            "credentialsConfigured": credentials_configured(),
            "graphVersion": META_GRAPH_VERSION,
            "feature": "Meta oEmbed public",
        }
