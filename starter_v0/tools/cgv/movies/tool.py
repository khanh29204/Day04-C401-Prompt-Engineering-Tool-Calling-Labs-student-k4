from __future__ import annotations

from typing import Any

from tools._shared import err
from tools.cgv._api import api_get, text_match
from tools.cgv._models import MovieListResponse


def cgv_movie_list(query: str = "", category: str = "all", limit: int = 20) -> dict[str, Any]:
    """List movies currently showing (or on sneak show) at CGV.

    `category` filters CGV's own grouping ("Now Showing", "Coming Soon", …);
    "all" keeps every group.
    """
    try:
        payload = MovieListResponse(**api_get("/api/movie/listSneakShow"))
        items: list[dict[str, Any]] = []
        categories: list[str] = []
        for movie in payload.data:
            if movie.category not in categories:
                categories.append(movie.category)
            if category not in {"", "all"} and not text_match(category, movie.category):
                continue
            if not text_match(query, movie.name):
                continue
            items.append({
                "sku": movie.sku,
                "movie_id": movie.id,
                "name": movie.name,
                "category": movie.category,
                "rating_code": movie.rating_code,
                "duration_minutes": movie.movie_endtime,
                "release_date": movie.release_date,
                "showing_date": movie.showing_date,
                "is_booking": movie.is_booking,
                "is_sneakshow": movie.is_sneakshow,
                "trailer": movie.movie_trailer,
            })
        limit = max(1, min(int(limit or 20), 100))
        return {
            "tool": "cgv_movies",
            "query": query,
            "category": category,
            "total_matches": len(items),
            "items": items[:limit],
            "truncated": len(items) > limit,
            "categories": categories,
        }
    except Exception as exc:
        return err("cgv_movies", exc)
