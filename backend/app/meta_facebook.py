from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

META_APP_ID = os.getenv("META_APP_ID", "").strip()
META_APP_SECRET = os.getenv("META_APP_SECRET", "").strip()
META_GRAPH_VERSION = os.getenv("META_GRAPH_VERSION", "v23.0").strip() or "v23.0"


def configured() -> bool:
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


def _candidate_urls(url: str) -> List[str]:
    out = [url]
    direct = _login_target(url)
    if direct:
        out.append(direct)
    try:
        response = requests.get(url, timeout=12, allow_redirects=False)
        location = response.headers.get("location")
        if location:
            absolute = urljoin(url, location)
            target = _login_target(absolute)
            if target:
                out.append(target)
    except Exception:
        pass
    return list(dict.fromkeys(x for x in out if x))


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).replace("\r", " ").replace("\n", " ").split()).strip()


def fetch_post(url: str) -> Dict[str, Any]:
    if not configured() or not url or not _is_facebook_url(url):
        return {}

    endpoint = f"https://graph.facebook.com/{META_GRAPH_VERSION}/oembed_post"
    last_error: Dict[str, Any] = {}

    for candidate in _candidate_urls(url):
        try:
            response = requests.get(
                endpoint,
                params={
                    "url": candidate,
                    "access_token": f"{META_APP_ID}|{META_APP_SECRET}",
                    "omitscript": "true",
                },
                headers={"Accept": "application/json"},
                timeout=18,
            )
            data = response.json() if response.content else {}
        except Exception as exc:
            last_error = {"error_message": _clean(exc)[:240]}
            continue

        if not response.ok:
            error = data.get("error") if isinstance(data, dict) else None
            if isinstance(error, dict):
                last_error = {
                    "error_code": error.get("code"),
                    "error_message": _clean(error.get("message"))[:240],
                }
            else:
                last_error = {"error_code": response.status_code}
            continue

        markup = str(data.get("html") or "") if isinstance(data, dict) else ""
        visible = ""
        if markup:
            visible = _clean(BeautifulSoup(markup, "html.parser").get_text("\n", strip=True))
        return {
            "candidate_url": candidate,
            "author": _clean(data.get("author_name")) if isinstance(data, dict) else "",
            "description": visible[:24000],
            "html": markup,
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
            if "Meta oEmbed ufficiale" not in methods:
                methods.insert(0, "Meta oEmbed ufficiale")
            bundle["methods"] = methods
        elif not legacy.clean(bundle.get("description", "")):
            if not configured():
                warnings.append("Facebook blocca l'accesso anonimo: configura Meta oEmbed Read sul backend.")
            elif meta.get("error_code") == 10:
                warnings.append("Meta oEmbed Read richiede Advanced Access/App Review prima di poter leggere i post pubblici.")
            else:
                warnings.append("Meta non ha reso disponibile questo post tramite oEmbed: potrebbe non essere pubblico o supportato.")

        return bundle, list(dict.fromkeys(warnings)), transcription_used

    legacy.source_bundle = source_bundle_with_meta

    @legacy.app.get("/meta/status")
    def meta_status():
        return {
            "configured": configured(),
            "graphVersion": META_GRAPH_VERSION,
            "feature": "Meta oEmbed Read",
        }
