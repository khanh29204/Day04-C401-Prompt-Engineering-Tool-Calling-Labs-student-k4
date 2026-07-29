from __future__ import annotations

from typing import Any

from tools._shared import err
from tools.cgv._api import api_get, mask
from tools.cgv.session import require_session


# Secrets the profile endpoint echoes back; never surfaced to the model.
_SECRET_KEYS = {"access_token", "usersessionid", "token", "u_token"}
_PII_KEYS = {"telephone", "phone", "email", "member_card_number", "card_number", "referral_code"}


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if lowered in _SECRET_KEYS:
                continue
            clean[key] = mask(item, 4) if lowered in _PII_KEYS and isinstance(item, str) else _sanitize(item)
        return clean
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    return value


def cgv_profile() -> dict[str, Any]:
    """Customer profile (membership tier, points, cards). Requires web-app login."""
    try:
        session = require_session()
        response = api_get(f"/api/customer/profile/id/{session.customer_id}", u_token=session.u_token)
        return {
            "tool": "cgv_profile",
            "profile_id": session.customer_id,
            "profile": _sanitize(response.get("data", response) if isinstance(response, dict) else response),
            "errors": response.get("errors") if isinstance(response, dict) else None,
        }
    except Exception as exc:
        return err("cgv_profile", exc)
