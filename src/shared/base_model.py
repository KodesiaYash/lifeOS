"""
SQLAlchemy declarative base with standard columns for all models.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.shared.sql_types import UUIDType


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


def utcnow() -> datetime:
    """Timezone-aware timestamp default shared across models."""
    return datetime.now(UTC)


class TimestampedBase(Base):
    """
    Abstract base for all tables with standard columns.
    Provides: id, created_at, updated_at, deleted_at.
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
        onupdate=utcnow,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
