"""Server-side CGV authentication state for one web request.

This module is deliberately not a model tool. The web layer authenticates a
user, retains the returned ``CgvSession`` server-side, and wraps any agent tool
execution in ``session_scope``. Consequently the CGV token is never part of a
tool schema, model argument, or tool result.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from typing import Iterator

from tools.cgv._api import api_errors, api_post, generate_signature
from tools.cgv._models import LoginResponse


@dataclass(frozen=True)
class CgvSession:
    customer_id: str
    u_token: str = field(repr=False)
    fullname: str = ""
    member_level: str = ""


_current_session: ContextVar[CgvSession | None] = ContextVar("cgv_current_session", default=None)


@contextmanager
def session_scope(customer_id: str | int, u_token: str, *, fullname: str = "", member_level: str = "") -> Iterator[CgvSession]:
    """Bind a CGV session to this request/task only, then restore prior state."""
    session = CgvSession(str(customer_id).strip(), u_token, fullname, member_level)
    if not session.customer_id or not session.u_token:
        raise ValueError("CGV session requires customer_id and u_token.")
    token: Token[CgvSession | None] = _current_session.set(session)
    try:
        yield session
    finally:
        _current_session.reset(token)


def current_session() -> CgvSession | None:
    """Return this request's session, if the web layer installed one."""
    return _current_session.get()


def require_session() -> CgvSession:
    """Return the request session or a safe error that the agent can surface."""
    session = current_session()
    if session is None:
        raise PermissionError("Người dùng chưa đăng nhập trên web app.")
    return session


def session_from_env() -> CgvSession:
    """Development/CLI convenience; production web requests must use a scope."""
    customer_id = os.getenv("CGV_CUSTOMER_ID", "").strip()
    u_token = os.getenv("CGV_U_TOKEN", "").strip()
    if not customer_id or not u_token:
        raise PermissionError("Người dùng chưa đăng nhập trên web app.")
    return CgvSession(customer_id, u_token)


def authenticate(email: str, password: str) -> CgvSession:
    """Authenticate from the web backend and return a server-side session.

    Do not invoke this function from a model tool. The caller must retain the
    session/token in its own secure server-side store, then use ``session_scope``
    while executing an authenticated tool request.
    """
    email = email.strip()
    if not email or not password:
        raise ValueError("CGV email and password are required.")
    payload = LoginResponse(**api_post("/api/customer/login", {
        "email": email,
        "password": password,
        "auto": 0,
        "signature": generate_signature(f"{email}{password}"),
    }))
    if payload.data is None:
        details = api_errors(payload.errors) or [{"detail": "Login failed with no error detail."}]
        raise PermissionError(f"CGV login failed: {details}")
    data = payload.data
    return CgvSession(str(data.entity_id), data.access_token, data.fullname, data.member_level)
