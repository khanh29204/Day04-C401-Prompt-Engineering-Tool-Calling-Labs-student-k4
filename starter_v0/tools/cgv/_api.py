"""Shared HTTP client for the CGV mobile API.

Ported from the `cgv-mcp` MCP server (https://github.com/t-rekttt/cgv-mcp) into
this repo's in-process tool contract. Differences from the original:

* `requests` instead of `httpx`, so the CGV tools reuse the dependency the rest
  of `tools/` already uses.
* A legacy-TLS adapter. `www.cgv.vn` only negotiates TLS 1.2 with the RSA cipher
  `AES128-SHA`, which modern OpenSSL defaults reject with
  `SSLV3_ALERT_HANDSHAKE_FAILURE`. `_session()` lowers the security level for
  this host only.
* Date normalisation and PHP-style form flattening, which the original left to
  the caller.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
import ssl
from datetime import date as date_cls, timedelta
from typing import Any

import requests
from pydantic import BaseModel
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

from tools._shared import TIMEOUT, fold_text


USER_AGENT = "CGV Cinema/2.9.4 (iPhone; iOS 18.3.1; Scale/3.00)"
BASE_API_URL = "https://www.cgv.vn/en"
SIGNATURE_SECRET_KEY = "juBDKUIb9C8vfbV171hdMHwSzxo="
X_DEVICE = "iOS_18.3_2.9.4"
FORM_CONTENT_TYPE = "application/x-www-form-urlencoded"


class _LegacyTLSAdapter(HTTPAdapter):
    """Allow TLS 1.2 + `AES128-SHA`, which cgv.vn is the only endpoint to require."""

    def init_poolmanager(self, *args: Any, **kwargs: Any) -> Any:
        context = create_urllib3_context(ciphers="DEFAULT:@SECLEVEL=1")
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.maximum_version = ssl.TLSVersion.TLSv1_2
        kwargs["ssl_context"] = context
        return super().init_poolmanager(*args, **kwargs)


_http: requests.Session | None = None
def _session() -> requests.Session:
    global _http
    if _http is None:
        session = requests.Session()
        session.mount("https://www.cgv.vn", _LegacyTLSAdapter())
        _http = session
    return _http


def generate_signature(message: str, secret_key: str = SIGNATURE_SECRET_KEY) -> str:
    """HMAC-SHA256 of `X_DEVICE + message`, base64 encoded (CGV's scheme)."""
    digest = hmac.new(secret_key.encode("utf-8"), (X_DEVICE + message).encode("utf-8"), hashlib.sha256)
    return base64.b64encode(digest.digest()).decode("utf-8")


def _parse(response: requests.Response) -> Any:
    """Return the JSON body, even on 4xx.

    CGV answers a rejected login with HTTP 403 and a useful body:
    `{"errors": [{"code": 500, "detail": "Incorrect login information"}]}`.
    Raising on status would throw that away, so only non-JSON failures raise.
    """
    try:
        body = response.json()
    except ValueError:
        response.raise_for_status()
        raise
    if response.status_code >= 400 and not (isinstance(body, dict) and body.get("errors")):
        response.raise_for_status()
    return body


def api_get(path: str, *, u_token: str | None = None) -> Any:
    headers = {"User-Agent": USER_AGENT, "X-Device": X_DEVICE}
    if u_token:
        headers["U-Token"] = u_token
    return _parse(_session().get(BASE_API_URL + path, headers=headers, timeout=TIMEOUT))


def api_post(path: str, data: dict[str, Any], *, u_token: str | None = None) -> Any:
    headers = {"User-Agent": USER_AGENT, "X-Device": X_DEVICE, "Content-Type": FORM_CONTENT_TYPE}
    if u_token:
        headers["U-Token"] = u_token
    return _parse(_session().post(BASE_API_URL + path, headers=headers, data=flatten_form(data), timeout=TIMEOUT))



def flatten_form(payload: dict[str, Any]) -> dict[str, Any]:
    """Flatten nested dicts/lists into PHP-style form keys, e.g. `ticket[0][Qty]`.

    The original MCP server posted Python lists straight into the form body,
    which CGV's PHP backend cannot read. Booleans become 0/1 and None becomes "".
    """
    flat: dict[str, Any] = {}

    def walk(key: str, value: Any) -> None:
        if isinstance(value, BaseModel):
            value = value.model_dump()
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                walk(f"{key}[{sub_key}]", sub_value)
        elif isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                walk(f"{key}[{index}]", item)
        elif isinstance(value, bool):
            flat[key] = int(value)
        elif value is None:
            flat[key] = ""
        else:
            flat[key] = value

    for key, value in payload.items():
        walk(key, value)
    return flat


def normalize_date(value: str | int | None, style: str = "ddmmyyyy") -> str:
    """Accept today/tomorrow, YYYY-MM-DD, DD/MM/YYYY, DDMMYYYY or YYYYMMDD.

    CGV wants a different layout per endpoint: schedules use DDMMYYYY, the seat
    map uses YYYYMMDD, concession uses DD/MM/YYYY.
    """
    raw = str(value or "").strip().lower()
    if raw in {"", "today", "hom nay", "hôm nay"}:
        day = date_cls.today()
    elif raw in {"tomorrow", "mai", "ngay mai", "ngày mai"}:
        day = date_cls.today() + timedelta(days=1)
    else:
        digits = re.sub(r"\D", "", raw)
        if len(digits) != 8:
            raise ValueError(f"Unrecognised date {value!r}; use YYYY-MM-DD, DD/MM/YYYY, DDMMYYYY or 'today'.")
        if 2000 <= int(digits[:4]) <= 2100:
            year, month, dom = int(digits[:4]), int(digits[4:6]), int(digits[6:])
        else:
            dom, month, year = int(digits[:2]), int(digits[2:4]), int(digits[4:])
        day = date_cls(year, month, dom)

    if style == "ddmmyyyy":
        return day.strftime("%d%m%Y")
    if style == "yyyymmdd":
        return day.strftime("%Y%m%d")
    if style == "slash":
        return day.strftime("%d/%m/%Y")
    if style == "iso":
        return day.strftime("%Y-%m-%d")
    raise ValueError(f"Unknown date style {style!r}")


def text_match(needle: str, haystack: str) -> bool:
    """Diacritic-insensitive substring match ("son la" matches "Sơn La")."""
    if not needle:
        return True
    return fold_text(needle).strip() in fold_text(haystack)


def mask(value: str, keep: int = 3) -> str:
    """Mask all but the last `keep` characters, for PII in tool output."""
    text = str(value or "")
    if len(text) <= keep:
        return "*" * len(text)
    return "*" * (len(text) - keep) + text[-keep:]


def compact_formats(languages: Any) -> list[dict[str, Any]]:
    """Shrink CGV's `languages[].sessions[]` tree to the fields a booking flow needs.

    The raw payload is ~45 KB per cinema; everything dropped here (icons, colours,
    service links) is unusable by a text agent.
    """
    formats: list[dict[str, Any]] = []
    for language in languages or []:
        formats.append({
            "format": language.name,
            "code": language.code,
            "sessions": [{
                "session_id": session.id,
                "time": session.time,
                "end_time": session.cinox_endtime,
                "room": session.room,
                "showing_type": session.showing_type,
                "remaining_seats": session.remaining_seats,
                "is_booking": session.is_booking,
            } for session in language.sessions],
        })
    return formats


def api_errors(errors: Any) -> list[dict[str, Any]] | None:
    """Normalise CGV's `errors` array (present on auth/seatmap failures)."""
    if not errors:
        return None
    return [item.model_dump() if isinstance(item, BaseModel) else item for item in errors]
