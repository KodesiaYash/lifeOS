"""
SQLAlchemy models for the knowledge store.

Single-user mode: No tenant_id or user_id references.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.base_model import TimestampedBase, utcnow
from src.shared.sql_types import JSONType, StringListType, UUIDType, vector_type


class KnowledgeDocument(TimestampedBase):
    """Metadata for ingested knowledge documents."""

    __tablename__ = "know_documents"

    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    title: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    author: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_points: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    storage_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    domain_tags: Mapped[list[str]] = mapped_column(StringListType, nullable=False, default=list)
    topic_tags: Mapped[list[str]] = mapped_column(StringListType, nullable=False, default=list)
    user_tags: Mapped[list[str]] = mapped_column(StringListType, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_channel: Mapped[str | None] = mapped_column(String(50), nullable=True)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now()
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONType, nullable=False, default=dict)


class KnowledgeChunk(TimestampedBase):
    """Text chunks with embeddings for vector search."""

    __tablename__ = "know_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("know_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    embedding = Column(vector_type(1536), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONType, nullable=False, default=dict)


class KnowledgeRelation(TimestampedBase):
    """Entity and topic relationships extracted from knowledge."""

    __tablename__ = "know_relations"

    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("know_documents.id", ondelete="CASCADE"), nullable=True
    )
    entity_name: Mapped[str] = mapped_column(String(500), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    related_to: Mapped[str | None] = mapped_column(String(500), nullable=True)
    relation_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONType, nullable=False, default=dict)
