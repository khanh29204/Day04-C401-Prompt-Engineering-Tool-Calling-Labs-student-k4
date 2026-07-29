---
name: cgv_seatmap
track: bonus
kind: live_api
provider: CGV Cinema mobile API (unofficial)
requires_env: []
inputs: [cinema_id, session_id, date, status_filter, limit]
outputs: [rows, status_counts, prices, total_seats]
side_effect: false
---
# cgv_seatmap

`POST /en/api/ticket/seatmap`, signed over `cinema_id + session_id +
customer_id` and sent with the `U-Token` header. Ported from `get_seatmap`.

Requires the user to be logged in on the web app. The web backend binds the
customer ID and CGV token to the current request with `session_scope()`; neither
value is an input or may be passed by the model. Without that server-side
session, the tool returns `Người dùng chưa đăng nhập trên web app.`

`cinema_id` and `session_id` come from `cgv_cinema_schedules` or
`cgv_movie_schedules`; `date` must be the session's own date (any accepted
format — it is converted to CGV's YYYYMMDD here).

Each seat keeps the fields a booking payload needs: `id`, `col`, `row`,
`areanumber`, `areacode`, `areacat_code`, `ticket_type_code`, `ttype_code`,
`price`, `price_u22`, `status`. Empty and null fields are dropped.

`status` codes are not documented by CGV, so this tool does not guess which
value means "free". Read `status_counts` first, then re-call with
`status_filter` set to the value you want.
