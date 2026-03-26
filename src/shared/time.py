"""
Timezone utilities for consistent datetime handling across the platform.
"""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo


def utc_now() -> datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


def to_user_tz(dt: datetime, tz_name: str = "UTC") -> datetime:
    """Convert a UTC datetime to the user's timezone."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(ZoneInfo(tz_name))


def start_of_day(dt: datetime, tz_name: str = "UTC") -> datetime:
    """Return start of day (00:00:00) in the given timezone, as UTC."""
    local = to_user_tz(dt, tz_name)
    start = local.replace(hour=0, minute=0, second=0, microsecond=0)
    return start.astimezone(UTC)


def end_of_day(dt: datetime, tz_name: str = "UTC") -> datetime:
    """Return end of day (23:59:59.999999) in the given timezone, as UTC."""
    local = to_user_tz(dt, tz_name)
    end = local.replace(hour=23, minute=59, second=59, microsecond=999999)
    return end.astimezone(UTC)
