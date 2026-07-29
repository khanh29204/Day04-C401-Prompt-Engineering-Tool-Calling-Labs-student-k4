---
name: cgv_cinemas
track: bonus
kind: live_api
provider: CGV Cinema mobile API (unofficial)
requires_env: []
inputs: [city, query, limit]
outputs: [items, total_matches, cities]
side_effect: false
---
# cgv_cinemas

`GET /en/api/cinema/list` — every CGV cinema grouped by city. Ported from the
`get_cinema_list` MCP tool.

Returns `cinema_id` (the value `cgv_cinema_schedules` and `cgv_seatmap` need),
name, city, address and special formats (IMAX, 4DX, Sweetbox…). Latitude,
longitude and poster URLs are dropped — the raw response is ~45 KB.

`city` and `query` are diacritic-insensitive substring filters, so `city="ho chi
minh"` matches `Hồ Chí Minh`. `cities` always lists every city in the response so
the agent can retry with a valid name after an empty match.
