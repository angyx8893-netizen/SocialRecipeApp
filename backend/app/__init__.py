"""SocialRecipe backend package helpers.

Facebook often turns /share/... links into /login/?next=<real public post> when
requested from a server.  The backend must not bypass private/login-only content,
but for genuinely public posts we can safely unwrap the canonical target and try
Facebook's public/mobile representations before giving up.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import requests

_ORIGINAL_GET = requests.get
_FACEBOOK_CRAWLER_UA = "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"


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


def _variants(value: str) -> List[str]:
    try:
        parsed = urlparse(value)
        if not _is_facebook_url(value):
            return [value]
        path = parsed.path or "/"
        suffix = ("?" + parsed.query) if parsed.query else ""
        return list(dict.fromkeys([
            value,
            f"https://www.facebook.com{path}{suffix}",
            f"https://m.facebook.com{path}{suffix}",
            f"https://mbasic.facebook.com{path}{suffix}",
        ]))
    except Exception:
        return [value]


def _looks_like_login(response: requests.Response) -> bool:
    location = response.headers.get("location", "")
    if location:
        absolute = urljoin(response.url or "https://www.facebook.com/", location)
        if _login_target(absolute):
            return True
        try:
            if "/login" in urlparse(absolute).path.lower():
                return True
        except Exception:
            pass
    try:
        if "/login" in urlparse(response.url or "").path.lower():
            return True
    except Exception:
        pass
    if response.status_code == 200:
        try:
            sample = (response.text or "")[:180000].lower()
        except Exception:
            sample = ""
        markers = (
            'id="login_form"',
            'name="email"',
            'name="pass"',
            "log into facebook",
            "accedi a facebook",
        )
        if sum(marker in sample for marker in markers) >= 2:
            return True
    return False


def _public_rescue(value: str, kwargs: Dict) -> Optional[requests.Response]:
    queue: List[str] = []
    target = _login_target(value)
    if target:
        queue.extend(_variants(target))
    queue.extend(_variants(value))

    base_headers = dict(kwargs.get("headers") or {})
    timeout = kwargs.get("timeout", 18)
    request_kwargs = dict(kwargs)
    request_kwargs.pop("headers", None)
    request_kwargs.pop("timeout", None)
    request_kwargs["allow_redirects"] = False

    seen = set()
    for candidate in queue:
        if candidate in seen or not _is_facebook_url(candidate):
            continue
        seen.add(candidate)
        for ua in (base_headers.get("User-Agent"), _FACEBOOK_CRAWLER_UA):
            headers = dict(base_headers)
            if ua:
                headers["User-Agent"] = ua
            try:
                response = _ORIGINAL_GET(candidate, headers=headers, timeout=timeout, **request_kwargs)
            except Exception:
                continue

            location = response.headers.get("location")
            if location:
                absolute = urljoin(candidate, location)
                login_target = _login_target(absolute)
                if login_target:
                    queue.extend(x for x in _variants(login_target) if x not in seen)
                    continue

            if response.ok and not _looks_like_login(response):
                return response
    return None


def _facebook_aware_get(url, *args, **kwargs):
    response = _ORIGINAL_GET(url, *args, **kwargs)
    if not isinstance(url, str) or not _is_facebook_url(url):
        return response

    location = response.headers.get("location")
    absolute = urljoin(url, location) if location else (response.url or url)
    if _login_target(absolute) or _looks_like_login(response):
        rescued = _public_rescue(_login_target(absolute) or url, kwargs)
        if rescued is not None:
            return rescued
    return response


# Package import happens before app.main is executed, therefore main.py's
# requests.get calls automatically benefit from this public-Facebook resolver.
requests.get = _facebook_aware_get
