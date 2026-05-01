"""
Service layer for scoped memory CRUD and retrieval.

General memory is shared across domains. Scoped memory belongs to a
specific domain namespace such as ``dutch_tutor``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from src.config import settings
from src.knowledge.embedding import EmbeddingService
from src.memory.assembler import MemoryAssembler
from src.memory.repository import MemoryFactRepository, SemanticMemoryRepository
from src.memory.schemas import (
    MemoryFactCreate,
    ScopedMemoryPacket,
    SemanticMemoryCreate,
)
from src.memory.semantic import SemanticMemoryStore
from src.memory.structured import StructuredMemory

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

GENERAL_MEMORY_NAMESPACE = "general"


class MemoryService:
    """High-level CRUD and retrieval service for shared and domain memory."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.structured = StructuredMemory(session)
        self.semantic = SemanticMemoryStore(session)
        self.assembler = MemoryAssembler(session)
        self.facts_repo = MemoryFactRepository(session)
        self.semantic_repo = SemanticMemoryRepository(session)
        self.embedding_service = EmbeddingService()

    @staticmethod
    def normalize_namespace(namespace: str | None) -> str:
        """Default empty namespace values to the shared general namespace."""
        return (namespace or GENERAL_MEMORY_NAMESPACE).strip() or GENERAL_MEMORY_NAMESPACE

    async def upsert_fact(
        self,
        *,
        namespace: str | None,
        category: str,
        key: str,
        value: str,
        structured_value: dict | None = None,
        confidence: float = 1.0,
        source: str = "api",
    ):
        """Create or supersede a structured fact inside a namespace."""
        normalized = self.normalize_namespace(namespace)
        return await self.structured.remember(
            MemoryFactCreate(
                domain=normalized,
                category=category,
                key=key,
                value=value,
                structured_value=structured_value,
                confidence=confidence,
                source=source,
            )
        )

    async def list_facts(
        self,
        *,
        namespace: str | None = None,
        category: str | None = None,
    ):
        """List active structured facts for a namespace."""
        normalized = self.normalize_namespace(namespace)
        if category is not None:
            return await self.facts_repo.list_by_category(category=category, domain=normalized)
        return await self.facts_repo.list_all_active(domain=normalized)

    async def delete_fact(self, fact_id: uuid.UUID):
        """Soft-delete a structured fact."""
        return await self.structured.forget(fact_id)

    async def store_semantic_memory(
        self,
        *,
        namespace: str | None,
        memory_type: str,
        content: str,
        related_domains: list[str] | None = None,
        confidence: float = 1.0,
        importance: float = 0.5,
        metadata: dict | None = None,
        with_embedding: bool = True,
    ):
        """Create a semantic memory inside a namespace."""
        normalized = self.normalize_namespace(namespace)
        embedding = None
        if with_embedding and settings.OPENAI_API_KEY:
            try:
                embedding = await self.embedding_service.embed_text(content)
            except Exception:
                logger.warning("semantic_embedding_skipped", namespace=normalized, memory_type=memory_type)

        return await self.semantic.store(
            SemanticMemoryCreate(
                memory_type=memory_type,
                content=content,
                source_domain=normalized,
                related_domains=related_domains or [normalized],
                confidence=confidence,
                importance=importance,
                metadata=metadata or {},
            ),
            embedding=embedding,
        )

    async def list_semantic_memories(
        self,
        *,
        namespace: str | None = None,
        limit: int = 50,
    ):
        """List semantic memories for a namespace."""
        normalized = self.normalize_namespace(namespace)
        return await self.semantic.list_memories(domain=normalized, limit=limit)

    async def delete_semantic_memory(self, memory_id: uuid.UUID):
        """Soft-delete a semantic memory."""
        return await self.semantic.forget(memory_id)

    async def retrieve_scoped_context(
        self,
        *,
        namespace: str,
        query: str,
        session_id: str | None = None,
        general_namespace: str = GENERAL_MEMORY_NAMESPACE,
    ) -> ScopedMemoryPacket:
        """Retrieve combined shared and domain-scoped context."""
        normalized_namespace = self.normalize_namespace(namespace)
        normalized_general = self.normalize_namespace(general_namespace)

        query_embedding = None
        if settings.OPENAI_API_KEY:
            try:
                query_embedding = await self.embedding_service.embed_text(query)
            except Exception:
                logger.warning("memory_retrieval_embedding_skipped", namespace=normalized_namespace)

        return await self.assembler.assemble_scoped(
            namespace=normalized_namespace,
            general_namespace=normalized_general,
            query_embedding=query_embedding,
            session_id=session_id,
        )
