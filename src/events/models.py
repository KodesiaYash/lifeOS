"""
SQLAlchemy model for the event log (evt_events).

Single-user mode: No tenant_id or user_id references.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.base_model import Base


class Event(Base):
    __tablename__ = "evt_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    event_type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    event_category: Mapped[str] = mapped_column(String(50), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(100), nullable=True)
    correlation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    causation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    importance: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
