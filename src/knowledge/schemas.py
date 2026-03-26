"""
Pydantic schemas for the knowledge store.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class KnowledgeDocumentCreate(BaseModel):
    source_type: str  # 'url', 'file_upload', 'note', 'browser_capture'
    url: str | None = None
    title: str | None = None
    author: str | None = None
    description: str | None = None
    content_type: str | None = None
    language: str | None = None
    domain_tags: list[str] = Field(default_factory=list)
    user_tags: list[str] = Field(default_factory=list)
    source_channel: str | None = None


class KnowledgeDocumentRead(BaseModel):
    id: uuid.UUID
    source_type: str
    url: str | None
    title: str | None
    summary: str | None
    status: str
    chunk_count: int
    domain_tags: list[str]
    topic_tags: list[str]
    user_tags: list[str]
    captured_at: datetime
    processed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeChunkRead(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    text: str
    token_count: int | None

    model_config = {"from_attributes": True}
