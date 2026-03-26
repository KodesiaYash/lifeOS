"""
Pagination utilities for list endpoints.
"""
from dataclasses import dataclass
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for paginated list endpoints."""
    offset: int = Field(default=0, ge=0, description="Number of items to skip")
    limit: int = Field(default=50, ge=1, le=200, description="Max items to return")


@dataclass
class PaginatedResult(Generic[T]):
    """Generic paginated result container."""
    items: list[T]
    total: int
    offset: int
    limit: int

    @property
    def has_more(self) -> bool:
        return self.offset + self.limit < self.total
