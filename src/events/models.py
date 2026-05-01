"""
SQLAlchemy model for the event log (evt_events).

Single-user mode: No tenant_id or user_id references.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.base_model import Base, utcnow
from src.shared.sql_types import JSONType, UUIDType


class Event(Base):
    __tablename__ = "evt_events"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    event_category: Mapped[str] = mapped_column(String(50), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(100), nullable=True)
    correlation_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True, index=True)
    causation_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)
    payload: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONType, nullable=False, default=dict)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    importance: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now()
    )
