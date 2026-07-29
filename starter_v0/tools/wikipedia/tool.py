from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, err

API_URL = "https://{lang}.wikipedia.org/w/api.php"
USER_AGENT = "AI20k-Day04-Research-Agent/1.0 (educational lab; contact: local)"
LANGUAGE_PRIORITY = ["vi", "en"]


def _wikipedia_get(lang: str, params: dict[str, Any]) -> dict[str, Any]:
    response = requests.get(
        API_URL.format(lang=lang),
        params={**params, "format": "json"},
        headers={"User-Agent": USER_AGENT},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def _search_titles(lang: str, query: str, limit: int) -> list[str]:
    data = _wikipedia_get(lang, {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": limit,
    })
    return [item["title"] for item in data.get("query", {}).get("search", [])]


def _fetch_summaries(lang: str, titles: list[str]) -> dict[str, Any]:
    if not titles:
        return {}
    data = _wikipedia_get(lang, {
        "action": "query",
        "prop": "extracts|info",
        "exintro": 1,
        "explaintext": 1,
        "inprop": "url",
        "redirects": 1,
        "titles": "|".join(titles),
    })
    return data.get("query", {}).get("pages", {})


def wikipedia_search(query: str = "", language: str = "auto", max_results: int = 3) -> dict[str, Any]:
    try:
        query = (query or "").strip()
        if not query:
            raise ValueError("query must not be empty")
        max_results = max(1, min(int(max_results or 3), 10))

        languages = [language] if language in ("vi", "en") else LANGUAGE_PRIORITY

        for lang in languages:
            titles = _search_titles(lang, query, max_results)
            if not titles:
                continue

            pages = _fetch_summaries(lang, titles)
            order = {title: index for index, title in enumerate(titles)}
            items = sorted(
                (page for page in pages.values() if "missing" not in page),
                key=lambda page: order.get(page.get("title"), len(order)),
            )
            results = [{
                "title": page.get("title"),
                "summary": (page.get("extract") or "").strip(),
                "url": page.get("fullurl"),
                "language": lang,
            } for page in items]

            if results:
                return {
                    "tool": "wikipedia_search",
                    "query": query,
                    "language": lang,
                    "items": results,
                }

        return {"tool": "wikipedia_search", "query": query, "language": languages[-1], "items": []}
    except Exception as exc:
        return err("wikipedia_search", exc)
