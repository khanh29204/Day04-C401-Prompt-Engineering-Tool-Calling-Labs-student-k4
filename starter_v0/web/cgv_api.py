"""Minimal same-origin backend for CGV authentication and protected tools.

Run it with ``uvicorn web.cgv_api:app --reload`` from ``starter_v0``. The
browser receives only an opaque, HttpOnly cookie. CGV credentials and U-Token
are sent only from this backend to CGV and remain server-side.
"""

from __future__ import annotations

import os
import secrets
import time
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from threading import Lock
from typing import Iterator

from fastapi import Cookie, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from tools.cgv.profile.tool import cgv_profile
from tools.cgv.seatmap.tool import cgv_seatmap
from tools.cgv.session import CgvSession, authenticate, session_scope
from web.agent_api import create_agent_router


COOKIE_NAME = "cgv_web_session"
SESSION_TTL_SECONDS = 2 * 60 * 60


@dataclass(frozen=True)
class _StoredSession:
    session: CgvSession
    expires_at: float


class _SessionStore:
    """In-memory session store for local development.

    Deployments with more than one process must replace this with Redis or a
    database-backed store. The opaque browser cookie remains the lookup key; it
    never contains a CGV token.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, _StoredSession] = {}
        self._lock = Lock()

    def create(self, session: CgvSession) -> str:
        session_id = secrets.token_urlsafe(32)
        with self._lock:
            self._purge_expired()
            self._sessions[session_id] = _StoredSession(session, time.monotonic() + SESSION_TTL_SECONDS)
        return session_id

    def get(self, session_id: str | None) -> CgvSession | None:
        if not session_id:
            return None
        with self._lock:
            stored = self._sessions.get(session_id)
            if stored is None:
                return None
            if stored.expires_at <= time.monotonic():
                del self._sessions[session_id]
                return None
            return stored.session

    def revoke(self, session_id: str | None) -> None:
        if session_id:
            with self._lock:
                self._sessions.pop(session_id, None)

    def _purge_expired(self) -> None:
        now = time.monotonic()
        for session_id, stored in list(self._sessions.items()):
            if stored.expires_at <= now:
                del self._sessions[session_id]


class LoginRequest(BaseModel):
    email: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=1024)


class SeatmapRequest(BaseModel):
    cinema_id: str
    session_id: str
    date: str = ""
    status_filter: str = ""
    limit: int = Field(default=400, ge=1, le=2000)


def _configured_origins() -> list[str]:
    return [origin.strip() for origin in os.getenv("CGV_WEB_ALLOWED_ORIGINS", "").split(",") if origin.strip()]


def _cookie_secure() -> bool:
    """Secure by default; explicitly set false only for local HTTP development."""
    return os.getenv("CGV_WEB_COOKIE_SECURE", "true").strip().lower() not in {"0", "false", "no"}


store = _SessionStore()
app = FastAPI(title="CGV backend", docs_url=None, redoc_url=None)
origins = _configured_origins()
_cors_kwargs: dict[str, object] = {
    "allow_credentials": True,
    "allow_methods": ["GET", "POST"],
    "allow_headers": ["Content-Type"],
}
if origins and origins != ["*"]:
    _cors_kwargs["allow_origins"] = origins
else:
    # Default (and explicit "*"): reflect any request Origin. A literal
    # allow_origins=["*"] cannot be combined with allow_credentials in
    # browsers, so use a match-all regex instead to keep cookies working.
    _cors_kwargs["allow_origin_regex"] = ".*"
app.add_middleware(CORSMiddleware, **_cors_kwargs)


def _require_web_session(session_id: str | None) -> CgvSession:
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=401, detail="Người dùng chưa đăng nhập trên web app.")
    return session


@contextmanager
def cgv_scope_for_web_session(session_id: str | None) -> Iterator[CgvSession]:
    """Use this around an agent run that may call authenticated CGV tools."""
    session = _require_web_session(session_id)
    with session_scope(
        session.customer_id,
        session.u_token,
        fullname=session.fullname,
        member_level=session.member_level,
    ):
        yield session


@contextmanager
def optional_cgv_scope_for_web_session(session_id: str | None) -> Iterator[CgvSession | None]:
    """Install a CGV context when logged in; leave public agent tools usable otherwise."""
    session = store.get(session_id)
    if session is None:
        with nullcontext(None) as empty:
            yield empty
        return
    with session_scope(
        session.customer_id,
        session.u_token,
        fullname=session.fullname,
        member_level=session.member_level,
    ):
        yield session


@app.post("/api/cgv/login")
def login(payload: LoginRequest, response: Response) -> dict[str, object]:
    """Login server-side and set an opaque cookie; never return the CGV token."""
    try:
        session = authenticate(payload.email, payload.password)
    except (PermissionError, ValueError):
        # Do not reveal CGV's raw response or whether an email is registered.
        raise HTTPException(status_code=401, detail="Không thể đăng nhập CGV.") from None

    session_id = store.create(session)
    response.set_cookie(
        COOKIE_NAME,
        session_id,
        httponly=True,
        secure=_cookie_secure(),
        samesite="lax",
        max_age=SESSION_TTL_SECONDS,
        path="/",
    )
    return {
        "authenticated": True,
        "fullname": session.fullname,
        "member_level": session.member_level,
    }


@app.post("/api/cgv/logout", status_code=204)
def logout(response: Response, cgv_web_session: str | None = Cookie(default=None)) -> Response:
    store.revoke(cgv_web_session)
    response.delete_cookie(COOKIE_NAME, path="/")
    return response


@app.get("/api/cgv/session")
def session_status(cgv_web_session: str | None = Cookie(default=None)) -> dict[str, object]:
    """Return safe UI state for an existing opaque browser session."""
    session = store.get(cgv_web_session)
    if session is None:
        return {"authenticated": False}
    return {
        "authenticated": True,
        "fullname": session.fullname,
        "member_level": session.member_level,
    }


@app.get("/api/cgv/profile")
def profile(cgv_web_session: str | None = Cookie(default=None)) -> dict[str, object]:
    with cgv_scope_for_web_session(cgv_web_session):
        return cgv_profile()


@app.post("/api/cgv/seatmap")
def seatmap(payload: SeatmapRequest, cgv_web_session: str | None = Cookie(default=None)) -> dict[str, object]:
    with cgv_scope_for_web_session(cgv_web_session):
        return cgv_seatmap(**payload.model_dump())


app.include_router(
    create_agent_router(
        cookie_name=COOKIE_NAME,
        optional_cgv_scope=optional_cgv_scope_for_web_session,
    )
)
