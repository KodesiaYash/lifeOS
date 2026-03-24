"""
Pydantic schemas for the retrieval layer.
"""
import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class RetrievalStrategy(StrEnum):
    STRUCTURED = "structured"
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    MEMORY_ONLY = "memory_only"
    KNOWLEDGE_ONLY = "knowledge_only"
    ALL = "all"


class TimeRange(BaseModel):
    since: datetime | None = None
    until: datetime | None = None


class RetrievalRequest(BaseModel):
    """Request for retrieving relevant context from all sources."""
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    query: str
    query_embedding: list[float] | None = None

    # Filtering
    domains: list[str] | None = None
    memory_layers: list[str] = Field(default=["all"])
    event_types: list[str] | None = None
    time_range: TimeRange | None = None
    content_types: list[str] | None = None

    # Strategy
    strategy: RetrievalStrategy = RetrievalStrategy.HYBRID
    max_results: int = 20
    min_relevance_score: float = 0.3

    # Ranking modifiers
    recency_weight: float = 0.3
    importance_weight: float = 0.2
    diversity_factor: float = 0.1


class RetrievalResult(BaseModel):
    """A single retrieved item with metadata."""
    id: uuid.UUID
    source: str              # 'memory_fact', 'semantic_memory', 'knowledge_chunk', 'event'
    content: str
    relevance_score: float
    metadata: dict = Field(default_factory=dict)

    # Source-specific fields
    domain: str | None = None
    created_at: datetime | None = None
    document_title: str | None = None


class RetrievalResponse(BaseModel):
    """Full response from a retrieval operation."""
    results: list[RetrievalResult] = Field(default_factory=list)
    total_found: int = 0
    strategy_used: RetrievalStrategy = RetrievalStrategy.HYBRID
    query: str = ""
