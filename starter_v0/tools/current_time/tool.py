from __future__ import annotations

import os
from typing import Any
from datetime import datetime, timezone as dt_timezone, timedelta

import requests

from tools._shared import TIMEOUT, err


def get_current_time(timezone: str = "Asia/Ho_Chi_Minh") -> dict[str, Any]:
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
    
    try:
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
        try:
            # Fallback to local system time adjusted by timezone
            try:
                from zoneinfo import ZoneInfo
                tz_obj = ZoneInfo(tz_query)
                now = datetime.now(tz_obj)
            except Exception:
                # If zoneinfo isn't available or tz_query isn't standard, check for VN (+7)
                if tz_query == "Asia/Ho_Chi_Minh":
                    tz_obj = dt_timezone(timedelta(hours=7))
                    now = datetime.now(tz_obj)
                else:
                    # Fallback to system local time
                    now = datetime.now()
            
            return {
                "tool": "current_time",
                "timezone": tz_query,
                "datetime": now.isoformat(),
                "date": now.strftime("%m/%d/%Y"),
                "time": now.strftime("%H:%M"),
                "day_of_week": now.strftime("%A"),
                "note": f"Fallback to system time due to API/Network error: {type(exc).__name__}"
            }
        except Exception as fallback_exc:
            return err("current_time", exc)
