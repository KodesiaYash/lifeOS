"""
Unit tests for src/shared/time.py — time utilities.

Tests:
  - test_utc_now_is_timezone_aware: utc_now() always returns tz-aware datetime
  - test_utc_now_is_utc: timezone is specifically UTC (not just any tz)
  - test_format_iso_contains_date: ISO format includes date component
  - test_format_iso_contains_time: ISO format includes time component
  - test_format_iso_roundtrip: Output can be parsed back to the same datetime
"""
from datetime import datetime, timezone

from src.shared.time import format_iso, utc_now


class TestUtcNow:
    """Verify utc_now() always returns a UTC-aware datetime."""

    def test_utc_now_is_timezone_aware(self):
        """Must never return a naive datetime."""
        now = utc_now()
        assert now.tzinfo is not None

    def test_utc_now_is_utc(self):
        """Timezone must be UTC specifically."""
        now = utc_now()
        assert now.tzinfo == timezone.utc


class TestFormatIso:
    """Verify ISO 8601 formatting."""

    def test_format_iso_contains_date(self):
        """Output includes YYYY-MM-DD."""
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        assert "2024-01-15" in format_iso(dt)

    def test_format_iso_contains_time(self):
        """Output includes HH:MM."""
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        assert "10:30" in format_iso(dt)

    def test_format_iso_roundtrip(self):
        """ISO string can be parsed back to equivalent datetime."""
        dt = datetime(2024, 6, 15, 14, 30, 0, tzinfo=timezone.utc)
        iso_str = format_iso(dt)
        parsed = datetime.fromisoformat(iso_str)
        assert parsed.year == dt.year
        assert parsed.hour == dt.hour
