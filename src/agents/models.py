"""
SQLAlchemy models for the agent system.

Single-user mode: No tenant_id or user_id references.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.base_model import Base, TimestampedBase, utcnow
from src.shared.sql_types import JSONType, StringListType, UUIDType


class AgentDefinition(Base):
    """Global agent template definitions."""

    __tablename__ = "agent_definitions"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    agent_type: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    domain: Mapped[str | None] = mapped_column(String(100), nullable=True)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    model_preference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=2048)
    tools: Mapped[list[str]] = mapped_column(StringListType, nullable=False, default=list)
    capabilities: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now(), onupdate=utcnow
    )


class AgentExecution(TimestampedBase):
    """Runtime execution record for an agent invocation."""

    __tablename__ = "agent_executions"

    agent_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    correlation_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default="pending")
    input_data: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    output_data: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    tool_calls: Mapped[list[dict]] = mapped_column(JSONType, nullable=False, default=list)
    llm_calls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
