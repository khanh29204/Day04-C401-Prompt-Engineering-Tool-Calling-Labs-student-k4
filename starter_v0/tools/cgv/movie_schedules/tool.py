from __future__ import annotations

from typing import Any

from tools._shared import err
from tools.cgv._api import api_get, compact_formats, normalize_date, text_match
from tools.cgv._models import MovieScheduleResponse


def cgv_movie_schedules(
    sku: str | int = "",
    date: str = "",
    city: str = "",
    cinema_query: str = "",
    limit: int = 15,
) -> dict[str, Any]:
    """Showtimes for one movie (by SKU) on one date, across cinemas.

    `date` accepts today/tomorrow, YYYY-MM-DD, DD/MM/YYYY or DDMMYYYY. Without a
    `city` or `cinema_query` filter CGV returns every cinema in the country, so
    the result is capped by `limit`.
    """
    try:
        if not str(sku or "").strip():
            raise ValueError("`sku` is required; get it from the `cgv_movies` tool.")
        api_date = normalize_date(date, "ddmmyyyy")
        payload = MovieScheduleResponse(**api_get(f"/cinemas/catalog_mobile/movieSchedules/sku/{sku}/date/{api_date}"))

        items: list[dict[str, Any]] = []
        cities: list[str] = []
        schedule_date = ""
        for schedule in payload.data:
            schedule_date = schedule_date or schedule.date
            for location in schedule.locations:
                if location.name not in cities:
                    cities.append(location.name)
                if not text_match(city, location.name):
                    continue
                for cinema in location.cinemas:
                    if not text_match(cinema_query, cinema.name):
                        continue
                    items.append({
                        "cinema_id": cinema.id,
                        "cinema": cinema.name,
                        "city": location.name,
                        "formats": compact_formats(cinema.languages),
                    })

        limit = max(1, min(int(limit or 15), 100))
        return {
            "tool": "cgv_movie_schedules",
            "sku": str(sku),
            "date": schedule_date or normalize_date(date, "iso"),
            "city": city,
            "total_cinemas": len(items),
            "items": items[:limit],
            "truncated": len(items) > limit,
            "cities": cities,
        }
    except Exception as exc:
        return err("cgv_movie_schedules", exc)
