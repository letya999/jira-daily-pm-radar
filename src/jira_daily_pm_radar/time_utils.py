from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo


def now_tz(timezone: str = "Asia/Almaty") -> datetime:
    return datetime.now(ZoneInfo(timezone))


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        # Jira sometimes returns offsets like +0000.
        try:
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")
        except ValueError:
            return None


def days_between(start: datetime | None, end: datetime | None = None) -> int | None:
    if start is None:
        return None
    end_dt = end or datetime.now(tz=start.tzinfo or UTC)
    return max((end_dt - start).days, 0)


def resolve_since(value: str, timezone: str = "Asia/Almaty") -> datetime:
    value = value.strip().lower()
    current = now_tz(timezone)
    if value in {"yesterday", "-1d", "1d"}:
        return current - timedelta(days=1)
    if value in {"today", "startofday"}:
        return current.replace(hour=0, minute=0, second=0, microsecond=0)
    if value.endswith("d") and value[:-1].lstrip("-").isdigit():
        days = abs(int(value[:-1]))
        return current - timedelta(days=days)
    parsed = parse_datetime(value)
    if parsed:
        return parsed
    raise ValueError(f"Unsupported --since value: {value}")


def safe_filename_datetime(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")
