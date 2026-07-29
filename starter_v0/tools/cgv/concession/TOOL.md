---
name: cgv_concession
track: bonus
kind: live_api
provider: CGV Cinema mobile API (unofficial)
requires_env: []
inputs: [session_id, product, theater_id, session_date, ticket]
outputs: [items, total_combos, banner]
side_effect: false
---
# cgv_concession

`POST /en/api/ticket/getInfoConcession` — the popcorn/drink combos attached to a
session, with `combo_id` values that a booking payload's `info_combo` map needs.
Ported from `get_info_concession`.

Argument sources: `session_id` from a schedule tool, `product` = the movie's
`movie_id` (`MovieItem.id`, not the SKU), `theater_id` = `cinema_id`.
`session_date` accepts any of the usual formats and is converted to CGV's
DD/MM/YYYY. The web backend injects the customer ID and token with the current
request's `session_scope()`; they are not model inputs.

`ticket` is optional here. When supplied, entries are validated against
`TicketRequest` and posted as PHP-style form keys (`ticket[0][Seat][0][label]`).
The MCP original posted the Python list directly, which the backend could not
parse — `flatten_form()` in `tools/cgv/_api.py` fixes that.
