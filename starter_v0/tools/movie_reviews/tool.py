from __future__ import annotations

import os
from typing import Any

import requests

from tools._shared import TIMEOUT, err

API_BASE = "https://api.themoviedb.org/3"
POSTER_BASE = "https://image.tmdb.org/t/p/w342"


def _tmdb_get(path: str, params: dict[str, Any]) -> dict[str, Any]:
    key = os.getenv("TMDB_API_KEY")
    if not key:
        raise RuntimeError("Missing TMDB_API_KEY env var")
    response = requests.get(
        f"{API_BASE}{path}",
        params={**params, "api_key": key},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def _find_movie(title: str, year: int) -> dict[str, Any] | None:
    params: dict[str, Any] = {"query": title, "include_adult": False}
    if year:
        params["year"] = year
    results = _tmdb_get("/search/movie", params).get("results") or []
    return results[0] if results else None


def _review_item(raw: dict[str, Any]) -> dict[str, Any]:
    content = (raw.get("content") or "").strip()
    rating = (raw.get("author_details") or {}).get("rating")
    return {
        "author": raw.get("author") or "anonymous",
        "rating": rating,
        "summary": content[:500] + ("..." if len(content) > 500 else ""),
        "url": raw.get("url"),
        "date": (raw.get("created_at") or "")[:10],
    }


def search_movie_reviews(query: str = "", year: int = 0, max_results: int = 5) -> dict[str, Any]:
    try:
        query = (query or "").strip()
        if not query:
            raise ValueError("query must not be empty")
        max_results = max(1, min(int(max_results or 5), 20))

        movie = _find_movie(query, year)
        if not movie:
            return {"tool": "movie_reviews", "query": query, "movie": None, "items": []}

        movie_id = movie["id"]
        raw_items = _tmdb_get(f"/movie/{movie_id}/reviews", {"page": 1}).get("results") or []

        return {
            "tool": "movie_reviews",
            "query": query,
            "movie": {
                "title": movie.get("title"),
                "release_date": movie.get("release_date"),
                "vote_average": movie.get("vote_average"),
                "vote_count": movie.get("vote_count"),
                "overview": movie.get("overview"),
                "tmdb_id": movie_id,
                "poster_url": f"{POSTER_BASE}{movie['poster_path']}" if movie.get("poster_path") else None,
            },
            "items": [_review_item(item) for item in raw_items[:max_results]],
        }
    except Exception as exc:
        return err("movie_reviews", exc)
