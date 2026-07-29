---
name: movie_reviews
track: bonus
kind: live_api
provider: TMDb (The Movie Database) API
requires_env: [TMDB_API_KEY]
inputs: [query, year, max_results]
outputs: [movie, items]
side_effect: false
---
# movie_reviews

Looks up a movie by title (optionally disambiguated by `year`) via TMDb's
search endpoint, then fetches user-written reviews for the best match from
TMDb's `/movie/{id}/reviews` endpoint.

Requires a free API key from https://www.themoviedb.org/settings/api, set as
`TMDB_API_KEY`. Returns `movie: null` and an empty `items` list if no title
matches the query — the reviews endpoint is never called in that case.
