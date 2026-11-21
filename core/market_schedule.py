"""Market hours, weekend countdown, and personalized greeting helper."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict


def get_market_schedule_info(now_utc: datetime | None = None, local_now: datetime | None = None) -> Dict:
    utc = now_utc or datetime.now(timezone.utc)
    loc = local_now or datetime.now()

    hour_local = loc.hour
    if hour_local < 12:
        time_greeting = "Good Morning"
    elif hour_local < 17:
        time_greeting = "Good Afternoon"
    else:
        time_greeting = "Good Evening"

    greeting = f"{time_greeting}, Tatenda — {loc.strftime('%A, %d %b %Y')}"

    # Forex & Gold market hours: Sunday 22:00 UTC -> Friday 22:00 UTC
    wd = utc.weekday()  # Mon=0 .. Fri=4, Sat=5, Sun=6
    is_closed = (wd == 4 and utc.hour >= 22) or (wd == 5) or (wd == 6 and utc.hour < 22)

    if is_closed:
        days_until_sun = (6 - wd) % 7
        next_open = (utc + timedelta(days=days_until_sun)).replace(hour=22, minute=0, second=0, microsecond=0)
        if next_open <= utc:
            next_open += timedelta(days=7)
        seconds_to_open = max(0, int((next_open - utc).total_seconds()))
        status_message = f"Today is {loc.strftime('%A')} — Forex & Gold Markets are Closed for the Weekend"
    else:
        seconds_to_open = 0
        status_message = "Markets are Open — Live Scanning Active"

    return {
        "greeting": greeting,
        "day_name": loc.strftime("%A"),
        "is_weekend_closed": is_closed,
        "seconds_to_open": seconds_to_open,
        "status_message": status_message,
    }
