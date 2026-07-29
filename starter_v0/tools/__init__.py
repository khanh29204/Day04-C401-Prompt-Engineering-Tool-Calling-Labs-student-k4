from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# Folder names are intentionally vague to match the tool names students see.
# The imported function names are the underlying implementations (unchanged).
from .clarify.tool import ask_user
from .papers.tool import arxiv_search
from .paper_text.tool import get_arxiv_paper_text
from .timeline.tool import get_user_tweets
from .fetch.tool import read_url
from .format.tool import render_digest
from .policy.tool import search_company_policy
from .social_search.tool import search_tweets
from .send.tool import send_telegram
from .lookup.tool import web_search

# CGV cinema tools (ported from the cgv-mcp MCP server; see tools/cgv/README.md).
from .cgv.cinemas.tool import cgv_cinema_list
from .cgv.cinema_schedules.tool import cgv_cinema_schedules
from .cgv.concession.tool import cgv_concession
from .cgv.movies.tool import cgv_movie_list
from .cgv.movie_schedules.tool import cgv_movie_schedules
from .cgv.profile.tool import cgv_profile
from .cgv.seatmap.tool import cgv_seatmap
from .current_time.tool import get_current_time


# NOTE (starter_v0): tool names here are intentionally vague. These keys are the
# names the model sees AND the names data/eval_base.json + data/eval_research_extension.json
# match against. If a team renames a tool, it MUST stay in sync across ALL of:
#   artifacts/tools.yaml  ->  this dict  ->  data/eval_base.json + data/eval_research_extension.json
# Otherwise the eval raises "not declared in tools.yaml" or scores every call as a name mismatch.
TOOL_FUNCTIONS = {
    "clarify": ask_user,
    "timeline": get_user_tweets,
    "social_search": search_tweets,
    "lookup": web_search,
    "fetch": read_url,
    "format": render_digest,
    "send": send_telegram,
    "policy": search_company_policy,
    "papers": arxiv_search,
    "paper_text": get_arxiv_paper_text,
    "current_time": get_current_time,
    # CGV cinema tools (bonus track). Comment this block out — here and in
    # artifacts/tools.yaml — if the extra declarations disturb base-eval routing.
    "cgv_cinemas": cgv_cinema_list,
    "cgv_movies": cgv_movie_list,
    "cgv_movie_schedules": cgv_movie_schedules,
    "cgv_cinema_schedules": cgv_cinema_schedules,
    "cgv_seatmap": cgv_seatmap,
    "cgv_concession": cgv_concession,
    "cgv_profile": cgv_profile,
}


def load_tool_declarations(path: Path) -> list[dict[str, Any]]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))["tools"]


def to_openai_tools(declarations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "type": "function",
        "function": {
            "name": item["name"],
            "description": item.get("description", ""),
            "parameters": item.get("parameters", {"type": "object", "properties": {}}),
        },
    } for item in declarations]
