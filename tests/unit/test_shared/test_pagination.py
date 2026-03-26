"""Unit tests for src/shared/pagination.py — pagination utilities.

Tests:
  - test_defaults: Default offset=0, limit=50
  - test_custom_offset_limit: Custom offset/limit values work
  - test_paginated_result_has_more: has_more property works
  - test_paginated_result_empty: 0 items, 0 total, still valid
"""
from src.shared.pagination import PaginatedResult, PaginationParams


class TestPaginationParams:
    """Verify offset/limit defaults."""

    def test_defaults(self):
        """Default pagination: offset 0, limit 50."""
        params = PaginationParams()
        assert params.offset == 0
        assert params.limit == 50

    def test_custom_offset_limit(self):
        """Custom offset and limit values are accepted."""
        params = PaginationParams(offset=40, limit=20)
        assert params.offset == 40
        assert params.limit == 20

    def test_offset_zero_by_default(self):
        """Offset defaults to 0."""
        params = PaginationParams(limit=10)
        assert params.offset == 0


class TestPaginatedResult:
    """Verify paginated result container."""

    def test_paginated_result_has_more(self):
        """has_more is True when more items exist."""
        result = PaginatedResult(items=["a", "b", "c"], total=100, offset=0, limit=3)
        assert result.has_more is True
        assert len(result.items) == 3

    def test_paginated_result_no_more(self):
        """has_more is False when at end."""
        result = PaginatedResult(items=[1, 2], total=2, offset=0, limit=50)
        assert result.has_more is False

    def test_paginated_result_empty(self):
        """Zero items is valid."""
        result = PaginatedResult(items=[], total=0, offset=0, limit=50)
        assert result.has_more is False
