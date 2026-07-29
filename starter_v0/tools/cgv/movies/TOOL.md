---
name: cgv_movies
track: bonus
kind: live_api
provider: CGV Cinema mobile API (unofficial)
requires_env: []
inputs: [query, category, limit]
outputs: [items, total_matches, categories]
side_effect: false
---
# cgv_movies

`GET /en/api/movie/listSneakShow` — movies currently showing plus sneak shows.
Ported from the `get_movie_list` MCP tool.

The important output field is `sku` (e.g. `26016500`): `cgv_movie_schedules`
takes the SKU, not the title. `movie_id` is the separate product id used by the
concession and add-to-cart calls. Poster/thumbnail URLs are dropped.

`query` (title) and `category` are diacritic-insensitive substring filters;
`categories` lists CGV's own groupings present in the response.
