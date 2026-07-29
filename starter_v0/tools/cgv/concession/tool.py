from __future__ import annotations

from typing import Any

from tools._shared import err
from tools.cgv._api import api_post, normalize_date
from tools.cgv._models import ConcessionResponse, TicketRequest
from tools.cgv.session import require_session


def cgv_concession(
    session_id: str | int = "",
    product: str | int = "",
    theater_id: str | int = "",
    session_date: str = "",
    ticket: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Combos and concessions offered for one session. Requires web-app login.

    `ticket` is optional; when given, each entry is validated against CGV's
    TicketRequest shape before being posted.
    """
    try:
        missing = [name for name, value in
                   (("session_id", session_id), ("product", product), ("theater_id", theater_id))
                   if not str(value or "").strip()]
        if missing:
            raise ValueError(f"Missing required argument(s): {', '.join(missing)}.")
        session = require_session()
        tickets = [TicketRequest(**item).model_dump() for item in (ticket or [])]

        payload = ConcessionResponse(**api_post("/api/ticket/getInfoConcession", {
            "session[id]": session_id,
            "session[date]": normalize_date(session_date, "slash"),
            "product": product,
            "theater[id]": theater_id,
            "customer_id": session.customer_id,
            "ticket": tickets,
        }, u_token=session.u_token))

        combos = [{
            "combo_id": combo.id,
            "name": combo.name,
            "short_desc": combo.short_desc,
            "price": combo.price,
            "original_price": combo.o_price,
            "ticket_price": combo.tprice,
            "includes_tickets": combo.ticket,
            "type": combo.type,
            "remaining": combo.remaining_concession,
        } for combo in payload.data.concession]

        return {
            "tool": "cgv_concession",
            "session_id": str(session_id),
            "session_date": normalize_date(session_date, "iso"),
            "banner": payload.data.banner,
            "total_combos": len(combos),
            "items": combos,
        }
    except Exception as exc:
        return err("cgv_concession", exc)
