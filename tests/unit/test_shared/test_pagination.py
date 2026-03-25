"""
Unit tests for src/shared/pagination.py — pagination utilities.

Tests:
  - test_defaults: Default page=1, size=50
  - test_offset_calculation: offset = (page - 1) * size
  - test_paginated_result_pages: pages = ceil(total / size)
  - test_paginated_result_single_page: total <= size means 1 page
  - test_paginated_result_empty: 0 items, 0 total, still valid
  - test_custom_page_size: Non-default page/size values work
"""
from src.shared.pagination import PaginatedResult, PaginationParams


class TestPaginationParams:
    """Verify page/size defaults and offset calculation."""

    def test_defaults(self):
        """Default pagination: page 1, 50 items per page."""
        params = PaginationParams()
        assert params.page == 1
        assert params.size == 50

    def test_offset_calculation(self):
        """Offset must be (page - 1) * size for SQL OFFSET."""
        params = PaginationParams(page=3, size=20)
        assert params.offset == 40

    def test_custom_page_size(self):
        """Non-default values are accepted."""
        params = PaginationParams(page=5, size=10)
        assert params.page == 5
        assert params.offset == 40


class TestPaginatedResult:
    """Verify page count computation."""

    def test_paginated_result_pages(self):
        """100 items / 3 per page = 34 pages (ceil)."""
        result = PaginatedResult(items=["a", "b", "c"], total=100, page=2, size=3)
        assert result.pages == 34
        assert len(result.items) == 3

    def test_paginated_result_single_page(self):
        """If total fits in one page, pages == 1."""
        result = PaginatedResult(items=[1, 2], total=2, page=1, size=50)
        assert result.pages == 1

    def test_paginated_result_empty(self):
        """Zero items is valid."""
        result = PaginatedResult(items=[], total=0, page=1, size=50)
        assert result.pages == 0
