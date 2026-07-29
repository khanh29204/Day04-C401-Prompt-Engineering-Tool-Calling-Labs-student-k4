from __future__ import annotations

from typing import Any

from tools._shared import err
from tools.cgv._api import api_get, compact_formats, normalize_date, text_match
from tools.cgv._models import CinemaScheduleResponse


def cgv_cinema_schedules(
    cinema_id: str | int = "",
    date: str = "",
    movie_query: str = "",
    limit: int = 20,
) -> dict[str, Any]:
    """Showtimes at one cinema on one date, across movies.

    `date` accepts today/tomorrow, YYYY-MM-DD, DD/MM/YYYY or DDMMYYYY.
    """
    try:
        if not str(cinema_id or "").strip():
            raise ValueError("`cinema_id` is required; get it from the `cgv_cinemas` tool.")
        api_date = normalize_date(date, "ddmmyyyy")
        payload = CinemaScheduleResponse(**api_get(f"/cinemas/catalog_mobile/siteschedules/id/{cinema_id}/date/{api_date}"))

        items: list[dict[str, Any]] = []
        schedule_date = ""
        for schedule in payload.data:
            schedule_date = schedule_date or schedule.date
            for movie in schedule.movies:
                if not text_match(movie_query, movie.name):
                    continue
                items.append({
                    "sku": movie.sku,
                    "movie_id": movie.id,
                    "name": movie.name,
                    "rating_code": movie.rating_code,
                    "duration_minutes": movie.movie_endtime,
                    "formats": compact_formats(movie.languages),
                })

        limit = max(1, min(int(limit or 20), 100))
        return {
            "tool": "cgv_cinema_schedules",
            "cinema_id": str(cinema_id),
            "date": schedule_date or normalize_date(date, "iso"),
            "movie_query": movie_query,
            "total_movies": len(items),
            "items": items[:limit],
            "truncated": len(items) > limit,
        }
    except Exception as exc:
        return err("cgv_cinema_schedules", exc)
