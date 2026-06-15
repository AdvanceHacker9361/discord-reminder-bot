from __future__ import annotations

from datetime import datetime, timedelta, tzinfo
import re


RELATIVE_PATTERN = re.compile(r"^(?P<amount>\d+)\s*(?P<unit>[mhd])$", re.IGNORECASE)


def parse_local_datetime(value: str, timezone: tzinfo, *, now: datetime | None = None) -> datetime:
    normalized = value.strip()
    if not normalized:
        raise ValueError("datetime is required")

    relative_match = RELATIVE_PATTERN.match(normalized)
    if relative_match is not None:
        amount = int(relative_match.group("amount"))
        unit = relative_match.group("unit").lower()
        current = now or datetime.now(timezone)
        if unit == "m":
            return current + timedelta(minutes=amount)
        if unit == "h":
            return current + timedelta(hours=amount)
        return current + timedelta(days=amount)

    parsed = datetime.fromisoformat(normalized.replace(" ", "T", 1))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone)
    return parsed.astimezone(timezone)
