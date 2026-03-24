"""
Pydantic schemas for the memory fabric.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class MemoryFactCreate(BaseModel):
    domain: str | None = None
    category: str
    key: str
    value: str
    structured_value: dict | None = None
    confidence: float = 1.0
    source: str = "user_stated"


class MemoryFactRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    domain: str | None
    category: str
    key: str
    value: str
    structured_value: dict | None
    confidence: float
    source: str
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SemanticMemoryCreate(BaseModel):
    memory_type: str  # 'summary', 'pattern', 'insight', 'preference', 'observation'
    content: str
    source_domain: str | None = None
    related_domains: list[str] = Field(default_factory=list)
    confidence: float = 1.0
    importance: float = 0.5
    metadata: dict = Field(default_factory=dict)


class SemanticMemoryRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    memory_type: str
    content: str
    source_domain: str | None
    related_domains: list[str]
    confidence: float
    importance: float
    access_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class MemoryPacket(BaseModel):
    """
    Assembled memory context for an LLM call.
    Contains relevant memories from all layers, within a token budget.
    """
    user_facts: list[MemoryFactRead] = Field(default_factory=list)
    semantic_memories: list[SemanticMemoryRead] = Field(default_factory=list)
    recent_summaries: list[str] = Field(default_factory=list)
    session_context: dict = Field(default_factory=dict)
    total_tokens_estimate: int = 0
