from __future__ import annotations

import os
from typing import Any

import requests

from tools._shared import TIMEOUT, err


def get_current_time(timezone: str = "Asia/Ho_Chi_Minh") -> dict[str, Any]:
    try:
        # Standardize and map common Vietnam timezone inputs
        tz_map = {
            "vn": "Asia/Ho_Chi_Minh",
            "vietnam": "Asia/Ho_Chi_Minh",
            "viet nam": "Asia/Ho_Chi_Minh",
            "việt nam": "Asia/Ho_Chi_Minh",
            "hcm": "Asia/Ho_Chi_Minh",
            "saigon": "Asia/Ho_Chi_Minh",
            "gmt+7": "Asia/Ho_Chi_Minh",
            "utc+7": "Asia/Ho_Chi_Minh",
        }
        
        normalized_tz = timezone.strip().lower()
        tz_query = tz_map.get(normalized_tz, timezone)
        
        response = requests.get(
            f"https://timeapi.io/api/time/current/zone?timeZone={tz_query}",
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "tool": "current_time",
            "timezone": data.get("timeZone", tz_query),
            "datetime": data.get("dateTime"),
            "date": data.get("date"),
            "time": data.get("time"),
            "day_of_week": data.get("dayOfWeek"),
        }
    except Exception as exc:
        return err("current_time", exc)
