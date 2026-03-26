"""Unit tests for src/shared/time.py — time utilities.

Tests:
  - test_utc_now_is_timezone_aware: utc_now() always returns tz-aware datetime
  - test_utc_now_is_utc: timezone is specifically UTC (not just any tz)
  - test_to_user_tz: Convert UTC to user timezone
  - test_start_of_day: Get start of day in timezone
  - test_end_of_day: Get end of day in timezone
"""

from datetime import UTC, datetime

from src.shared.time import end_of_day, start_of_day, to_user_tz, utc_now


class TestUtcNow:
    """Verify utc_now() always returns a UTC-aware datetime."""

    def test_utc_now_is_timezone_aware(self):
        """Must never return a naive datetime."""
        now = utc_now()
        assert now.tzinfo is not None

    def test_utc_now_is_utc(self):
        """Timezone must be UTC specifically."""
        now = utc_now()
        assert now.tzinfo == UTC


class TestToUserTz:
    """Verify timezone conversion."""

    def test_to_user_tz_default_utc(self):
        """Default timezone is UTC."""
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
        result = to_user_tz(dt)
        assert result.tzinfo is not None
        assert result.hour == 10

    def test_to_user_tz_new_york(self):
        """Convert UTC to America/New_York."""
        dt = datetime(2024, 1, 15, 15, 0, 0, tzinfo=UTC)
        result = to_user_tz(dt, "America/New_York")
        assert result.tzinfo is not None
        # In January, NY is UTC-5
        assert result.hour == 10


class TestStartOfDay:
    """Verify start of day calculation."""

    def test_start_of_day_utc(self):
        """Start of day in UTC."""
        dt = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)
        result = start_of_day(dt, "UTC")
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0


class TestEndOfDay:
    """Verify end of day calculation."""

    def test_end_of_day_utc(self):
        """End of day in UTC."""
        dt = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)
        result = end_of_day(dt, "UTC")
        assert result.hour == 23
        assert result.minute == 59
        assert result.second == 59
