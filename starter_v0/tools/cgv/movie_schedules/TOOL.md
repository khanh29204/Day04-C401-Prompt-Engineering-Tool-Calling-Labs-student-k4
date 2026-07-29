---
name: cgv_movie_schedules
track: bonus
kind: live_api
provider: CGV Cinema mobile API (unofficial)
requires_env: []
inputs: [sku, date, city, cinema_query, limit]
outputs: [items, total_cinemas, date, cities]
side_effect: false
---
# cgv_movie_schedules

`GET /en/cinemas/catalog_mobile/movieSchedules/sku/{sku}/date/{DDMMYYYY}` —
"where and when can I watch this movie". Ported from `get_movie_schedules`.

`sku` comes from `cgv_movies`. Unlike the MCP original, `date` is normalised
here: `today`, `tomorrow`, `2026-07-30`, `30/07/2026` and `30072026` all work,
and an empty date means today.

Each item is one cinema with `formats[].sessions[]`; `session_id` is what
`cgv_seatmap` needs. CGV returns every cinema nationwide, so filter with `city`
or `cinema_query` — otherwise you get the first `limit` cinemas and
`truncated: true`.
