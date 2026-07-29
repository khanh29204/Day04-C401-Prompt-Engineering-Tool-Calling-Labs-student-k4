from __future__ import annotations

from collections import Counter
from typing import Any

from tools._shared import err
from tools.cgv._api import api_errors, api_post, generate_signature, normalize_date
from tools.cgv._models import SeatMapResponse
from tools.cgv.session import require_session


_DROP_FIELDS = {"seat_type_color", "areacat_intseq"}


def _compact_seat(seat: Any) -> dict[str, Any]:
    dumped = seat.model_dump(exclude=_DROP_FIELDS)
    return {key: value for key, value in dumped.items() if value not in (None, "")}


def cgv_seatmap(
    cinema_id: str | int = "",
    session_id: str | int = "",
    date: str = "",
    status_filter: str = "",
    limit: int = 400,
) -> dict[str, Any]:
    """Seat map and per-seat pricing for one session. Requires web-app login.

    `status_filter` keeps only seats whose `status` equals the given value; the
    `status_counts` summary shows which values the room actually uses.
    """
    try:
        if not str(cinema_id or "").strip() or not str(session_id or "").strip():
            raise ValueError("`cinema_id` and `session_id` are required; get them from a schedule tool.")
        session = require_session()
        api_date = normalize_date(date, "yyyymmdd")

        payload = SeatMapResponse(**api_post("/api/ticket/seatmap", {
            "cinema_id": cinema_id,
            "customer_id": session.customer_id,
            "date": api_date,
            "session_id": session_id,
            "signature": generate_signature(f"{cinema_id}{session_id}{session.customer_id}"),
        }, u_token=session.u_token))

        if payload.data is None:
            return {
                "tool": "cgv_seatmap",
                "session_id": str(session_id),
                "rows": [],
                "errors": api_errors(payload.errors) or [{"detail": "No seat map returned."}],
            }

        limit = max(1, min(int(limit or 400), 2000))
        status_counts: Counter[str] = Counter()
        prices: set[int] = set()
        rows: list[dict[str, Any]] = []
        kept = 0
        for row in payload.data:
            seats: list[dict[str, Any]] = []
            for seat in row.seats:
                status_counts[str(seat.status)] += 1
                if seat.price:
                    prices.add(seat.price)
                if status_filter and str(seat.status) != status_filter:
                    continue
                if kept >= limit:
                    continue
                seats.append(_compact_seat(seat))
                kept += 1
            if seats:
                rows.append({"label": row.label, "seats": seats})

        return {
            "tool": "cgv_seatmap",
            "cinema_id": str(cinema_id),
            "session_id": str(session_id),
            "date": normalize_date(date, "iso"),
            "status_filter": status_filter,
            "total_seats": sum(status_counts.values()),
            "status_counts": dict(status_counts),
            "prices": sorted(prices),
            "returned_seats": kept,
            "truncated": kept >= limit,
            "rows": rows,
        }
    except Exception as exc:
        return err("cgv_seatmap", exc)
