"""
Long-term semantic memory: pgvector-backed semantic store.
Stores summaries, patterns, insights, and behavioral observations with embeddings.
"""
import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.memory.models import SemanticMemory as SemanticMemoryModel
from src.memory.repository import SemanticMemoryRepository
from src.memory.schemas import SemanticMemoryCreate

logger = structlog.get_logger()


class SemanticMemoryStore:
    """
    pgvector-backed semantic memory layer.
    Stores natural language memories with embeddings for similarity search.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.repo = SemanticMemoryRepository(session)

    async def store(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        data: SemanticMemoryCreate,
        embedding: list[float] | None = None,
    ) -> SemanticMemoryModel:
        """Store a semantic memory with an optional pre-computed embedding."""
        memory = SemanticMemoryModel(
            tenant_id=tenant_id,
            user_id=user_id,
            memory_type=data.memory_type,
            content=data.content,
            embedding=embedding,
            source_domain=data.source_domain,
            related_domains=data.related_domains,
            confidence=data.confidence,
            importance=data.importance,
            metadata_=data.metadata,
        )
        memory = await self.repo.create(memory)
        logger.info(
            "semantic_memory_stored",
            memory_id=str(memory.id),
            memory_type=data.memory_type,
            has_embedding=embedding is not None,
        )
        return memory

    async def search(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        query_embedding: list[float],
        limit: int = 10,
        domain: str | None = None,
    ) -> list[SemanticMemoryModel]:
        """Search semantic memories by embedding similarity."""
        results = await self.repo.search_by_embedding(
            tenant_id=tenant_id,
            user_id=user_id,
            embedding=query_embedding,
            limit=limit,
            domain=domain,
        )
        # Track access for importance scoring
        for mem in results:
            await self.repo.increment_access(mem.id)
        return results
