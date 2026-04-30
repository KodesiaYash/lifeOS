"""
SQLAlchemy models for the memory fabric.

Single-user mode: No tenant_id or user_id references.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.base_model import TimestampedBase
from src.shared.sql_types import JSONType, StringListType, UUIDType, vector_type


class MemoryFact(TimestampedBase):
    """Long-term structured memory facts — discrete, retrievable pieces of information."""

    __tablename__ = "mem_facts"

    domain: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    structured_value: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    source: Mapped[str] = mapped_column(String(50), nullable=False, server_default="user_stated")
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    superseded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("mem_facts.id"), nullable=True
    )


class SemanticMemory(TimestampedBase):
    """Long-term semantic memories — summaries, patterns, insights."""

    __tablename__ = "mem_semantic_memories"

    memory_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = Column(vector_type(1536), nullable=True)
    source_domain: Mapped[str | None] = mapped_column(String(100), nullable=True)
    related_domains: Mapped[list[str]] = mapped_column(StringListType, nullable=False, default=list)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    importance: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    access_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    superseded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("mem_semantic_memories.id"), nullable=True
    )
    metadata_: Mapped[dict] = mapped_column("metadata", JSONType, nullable=False, default=dict)


class ConversationSummary(TimestampedBase):
    """Summaries of past conversation sessions."""

    __tablename__ = "mem_conversation_summaries"

    conversation_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    key_topics: Mapped[list[str]] = mapped_column(StringListType, nullable=False, default=list)
    domains_involved: Mapped[list[str]] = mapped_column(StringListType, nullable=False, default=list)
    turn_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    embedding = Column(vector_type(1536), nullable=True)
