# CGV cinema tools

Ported from the [`cgv-mcp`](https://github.com/t-rekttt/cgv-mcp) MCP server into
this repo's in-process tool contract. There is no MCP client, no stdio transport
and no separate process: `TOOL_FUNCTIONS` in `tools/__init__.py` calls these
functions directly, the same way it calls `lookup` or `papers`.

```text
tools/cgv/
  _api.py                 shared HTTP client, signing, date + form helpers
  _models.py              Pydantic response models (verbatim from the MCP server)
  session.py              server-side per-request CGV authentication context
  cinemas/                cgv_cinemas            <- get_cinema_list
  movies/                 cgv_movies             <- get_movie_list
  movie_schedules/        cgv_movie_schedules    <- get_movie_schedules
  cinema_schedules/       cgv_cinema_schedules   <- get_cinema_schedules
  seatmap/                cgv_seatmap            <- get_seatmap
  concession/             cgv_concession         <- get_info_concession
  profile/                cgv_profile            <- get_profile
```

Each leaf folder follows `tools/README.md`: `TOOL.md` (frontmatter + notes) plus
`tool.py`. The two `_`-prefixed modules are shared plumbing, mirroring
`tools/_shared.py`; they hold no tool entry point.

## Typical call chain

```text
cgv_movies(query="odyssey")            -> sku
cgv_movie_schedules(sku, date="today") -> cinema_id + session_id
cgv_seatmap(cinema_id, session_id, date) -> seats + prices
cgv_concession(session_id, product=movie_id, theater_id=cinema_id, session_date)
```

`cgv_cinemas` → `cgv_cinema_schedules` is the mirror route when the user starts
from a cinema instead of a movie.

## What changed from the MCP original

| Area | MCP server | Here |
| --- | --- | --- |
| Transport | `httpx`, one call per tool | `requests` session shared across tools (`_api.py`) |
| TLS | worked by luck of client defaults | explicit TLS 1.2 + `AES128-SHA` adapter, see below |
| Dates | caller had to send `DDMMYYYY` / `YYYYMMDD` / `DD/MM/YYYY` | `normalize_date()` accepts `today`, `tomorrow`, ISO, slashed or packed |
| Payloads | full API response (~45 KB for cinema list) | trimmed to fields a text agent can use, with `total_*` / `truncated` flags |
| Nested form data | Python lists posted raw (backend cannot parse) | `flatten_form()` emits PHP-style `ticket[0][Seat][0][label]` |
| Auth | `access_token` returned to the caller and printed | web backend stores it and binds it per request; never a tool input/output |
| Errors | exception propagated to the MCP client | `tools._shared.err()` dict, so the agent loop keeps going |

Two MCP tools were deliberately **not** ported: `add_tickets` and
`book_order_by_compound`. Upstream marks both as not working, and they are the
only ones that spend money.

## `www.cgv.vn` needs a legacy TLS handshake

The host negotiates TLS 1.2 only, and offers exactly one cipher —
`AES128-SHA` (RSA key exchange, no forward secrecy). Modern OpenSSL defaults
refuse it:

```text
SSLError(1, '[SSL: SSLV3_ALERT_HANDSHAKE_FAILURE] ssl/tls alert handshake failure')
```

`_LegacyTLSAdapter` in `_api.py` sets `@SECLEVEL=1` and pins TLS 1.2 for
`https://www.cgv.vn` only; every other host in this repo keeps the default,
stricter context.

## Web authentication and token isolation

The public tools (`cgv_cinemas`, `cgv_movies`, `cgv_movie_schedules`,
`cgv_cinema_schedules`) do not need an account. `cgv_seatmap`,
`cgv_concession`, and `cgv_profile` require the user to have logged in on the
web app.

The web backend receives the email and password, calls `authenticate()`, stores
the resulting `CgvSession` only on the server, then binds it around each agent
run. The token is deliberately absent from `tools.yaml`, Python tool signatures,
and tool outputs:

```python
from tools.cgv.session import authenticate, session_scope

# Web login endpoint: retain `session` in the server-side user session/vault.
session = authenticate(email, password)

# Agent request for that same authenticated user:
with session_scope(
    session.customer_id, session.u_token,
    fullname=session.fullname, member_level=session.member_level,
):
    result = cgv_seatmap(cinema_id="006", session_id="...", date="today")
```

Never return a token to the browser or include it in an agent message/history.

The four public tools (`cgv_cinemas`, `cgv_movies`, `cgv_movie_schedules`,
`cgv_cinema_schedules`) need no account and no API key.

## Turning these off

The eight declarations in `artifacts/tools.yaml` are visible to the model and can
shift routing on the base eval. To restore the original 10-tool surface, comment
out the CGV block in `artifacts/tools.yaml` **and** the matching block in
`tools/__init__.py`.

This is an unofficial, reverse-engineered mobile API used here for a lab
exercise. It can change or start rejecting requests without notice.
