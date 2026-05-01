"""
Core platform SQLAlchemy models for single-user mode.

Models: Settings, DomainRegistry.
No tenant/user models needed - the app runs for whoever is running it locally.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.base_model import Base, utcnow
from src.shared.sql_types import JSONType, StringListType, UUIDType


class Settings(Base):
    """
    Global application settings for single-user mode.
    Only one row should exist (singleton pattern).
    """

    __tablename__ = "core_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, server_default="UTC")
    language: Mapped[str] = mapped_column(String(10), nullable=False, server_default="en")
    preferences: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    active_domains: Mapped[list[str]] = mapped_column(StringListType, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now(), onupdate=utcnow
    )


class DomainRegistry(Base):
    """Registry of available domain plugins."""

    __tablename__ = "core_domain_registry"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    domain_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    manifest: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    config: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    installed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now(), onupdate=utcnow
    )
