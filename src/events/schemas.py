"""
Pydantic schemas for the platform event model.

Single-user mode: No tenant_id or user_id references.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PlatformEvent(BaseModel):
    """Canonical event schema for all domain and system events."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_type: str  # e.g., "health.meal_logged"
    event_category: str = "domain"  # "domain", "system", "communication"
    domain: str | None = None  # Source domain, None for system events
    correlation_id: uuid.UUID | None = None  # Links to triggering request
    causation_id: uuid.UUID | None = None  # Event that caused this event
    payload: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)
    source: str = "user_action"  # "user_action", "system", "scheduler", "connector"
    importance: float = 0.5  # 0-1
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EventQuery(BaseModel):
    """Query parameters for event retrieval."""

    event_type: str | None = None
    domain: str | None = None
    correlation_id: uuid.UUID | None = None
    since: datetime | None = None
    until: datetime | None = None
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
