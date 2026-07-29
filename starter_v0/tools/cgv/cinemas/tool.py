from __future__ import annotations

from typing import Any

from tools._shared import err
from tools.cgv._api import api_get, text_match
from tools.cgv._models import CinemaListResponse


def cgv_cinema_list(city: str = "", query: str = "", limit: int = 30) -> dict[str, Any]:
    """List CGV cinemas, optionally filtered by city name or free text.

    `query` matches the cinema name and address; both filters ignore diacritics.
    """
    try:
        payload = CinemaListResponse(**api_get("/api/cinema/list"))
        items: list[dict[str, Any]] = []
        cities: list[str] = []
        for group in payload.data:
            cities.append(group.name)
            if not text_match(city, group.name):
                continue
            for cinema in group.cinemas:
                if not text_match(query, f"{cinema.name} {cinema.address}"):
                    continue
                items.append({
                    "cinema_id": cinema.id,
                    "name": cinema.name,
                    "city": group.name,
                    "address": cinema.address.strip(),
                    "specials": [special.title for special in cinema.specials],
                })
        limit = max(1, min(int(limit or 30), 200))
        return {
            "tool": "cgv_cinemas",
            "city": city,
            "query": query,
            "total_matches": len(items),
            "items": items[:limit],
            "truncated": len(items) > limit,
            "cities": cities,
        }
    except Exception as exc:
        return err("cgv_cinemas", exc)
