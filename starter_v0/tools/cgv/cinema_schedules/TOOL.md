---
name: cgv_cinema_schedules
track: bonus
kind: live_api
provider: CGV Cinema mobile API (unofficial)
requires_env: []
inputs: [cinema_id, date, movie_query, limit]
outputs: [items, total_movies, date]
side_effect: false
---
# cgv_cinema_schedules

`GET /en/cinemas/catalog_mobile/siteschedules/id/{cinema_id}/date/{DDMMYYYY}` —
"what is playing at this cinema today". Ported from `get_cinema_schedules`.

`cinema_id` comes from `cgv_cinemas` (e.g. `006`) — keep the leading zero, it is
a string. `date` is normalised the same way as in `cgv_movie_schedules`.

Each item is one movie with `formats[].sessions[]`, where `session_id` feeds
`cgv_seatmap`. Use this tool when the user names a cinema; use
`cgv_movie_schedules` when they name a movie.
