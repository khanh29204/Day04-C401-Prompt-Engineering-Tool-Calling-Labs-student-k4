"""HTTP adapter for the existing research agent.

The adapter deliberately accepts only a chat message.  CGV credentials and
tokens are never request fields and never become model tool arguments.  The
hosting application supplies an *optional* request-scoped CGV context: public
cinema tools work without one, while protected tools see the server-side
session when the user has logged in.
"""

from __future__ import annotations

import os
from contextlib import AbstractContextManager
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

from fastapi import APIRouter, Cookie, HTTPException
from pydantic import BaseModel, Field

from chat import run_model_tool_loop
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT / "artifacts"
load_lab_env(ROOT)


class ChatRequest(BaseModel):
    """One user message plus a small, plaintext conversation history."""

    message: str = Field(min_length=1, max_length=8_000)
    history: list[dict[str, str]] = Field(default_factory=list, max_length=12)


class _AgentRuntime:
    def __init__(self) -> None:
        provider_name = os.getenv("CGV_AGENT_PROVIDER", "openai").strip().lower()
        if provider_name not in {"openai", "openrouter", "anthropic", "gemini"}:
            raise ValueError("CGV_AGENT_PROVIDER must be openai, openrouter, anthropic, or gemini.")
        self.provider = make_provider(provider_name)
        self.model = os.getenv("CGV_AGENT_MODEL", "").strip() or None
        self.system_prompt = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
        self.tools = to_openai_tools(load_tool_declarations(ARTIFACTS_DIR / "tools.yaml"))
        try:
            self.max_tool_rounds = max(1, min(int(os.getenv("CGV_AGENT_MAX_TOOL_ROUNDS", "4")), 8))
        except ValueError:
            self.max_tool_rounds = 4


@lru_cache(maxsize=1)
def _runtime() -> _AgentRuntime:
    """Create provider/tool declarations once per backend process."""
    return _AgentRuntime()


OptionalCgvScope = Callable[[str | None], AbstractContextManager[object]]


def create_agent_router(
    *,
    cookie_name: str,
    optional_cgv_scope: OptionalCgvScope,
) -> APIRouter:
    """Create the router without importing the host's session store.

    Passing the scope in avoids a circular import with ``web.cgv_api`` and
    makes the token boundary explicit at the integration point.
    """
    router = APIRouter()

    @router.post("/api/chat")
    def chat(payload: ChatRequest, cgv_web_session: str | None = Cookie(default=None, alias=cookie_name)) -> dict[str, Any]:
        runtime = _runtime()
        history = [
            {"role": item["role"], "content": item["content"][:8_000]}
            for item in payload.history
            if item.get("role") in {"user", "assistant"} and item.get("content", "").strip()
        ][-10:]
        try:
            # The model receives only the user message and tool schemas.  The
            # server installs the CGV session around execution, never in either.
            with optional_cgv_scope(cgv_web_session):
                result = run_model_tool_loop(
                    provider=runtime.provider,
                    messages=[
                        {"role": "system", "content": runtime.system_prompt},
                        *history,
                        {"role": "user", "content": payload.message.strip()},
                    ],
                    tools=runtime.tools,
                    model=runtime.model,
                    max_tool_rounds=runtime.max_tool_rounds,
                )
        except ValueError as exc:
            # Configuration errors are actionable to the developer but should
            # not expose CGV/provider internals to the browser.
            raise HTTPException(status_code=500, detail=f"Agent configuration error: {exc}") from None
        except Exception:
            raise HTTPException(status_code=502, detail="Agent không thể xử lý yêu cầu lúc này.") from None

        # tool_events are intentional UI activity data.  CGV tool signatures do
        # not contain tokens; protected-tool results sanitize token fields.
        return {
            "status": result["status"],
            "assistant_text": result["assistant_text"],
            "tool_events": result["tool_events"],
        }

    return router
