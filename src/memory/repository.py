"""
Database access layer for memory entities.

Single-user mode: No tenant_id or user_id filtering.
"""

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.memory.models import ConversationSummary, MemoryFact, SemanticMemory


class MemoryFactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, fact: MemoryFact) -> MemoryFact:
        self.session.add(fact)
        await self.session.flush()
        return fact

    async def get_by_key(self, key: str) -> MemoryFact | None:
        result = await self.session.execute(
            select(MemoryFact).where(
                MemoryFact.key == key,
                MemoryFact.active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_category(
        self,
        category: str,
        domain: str | None = None,
    ) -> list[MemoryFact]:
        stmt = select(MemoryFact).where(
            MemoryFact.category == category,
            MemoryFact.active.is_(True),
        )
        if domain is not None:
            stmt = stmt.where(MemoryFact.domain == domain)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all_active(self, domain: str | None = None) -> list[MemoryFact]:
        stmt = select(MemoryFact).where(MemoryFact.active.is_(True))
        if domain is not None:
            stmt = stmt.where(MemoryFact.domain == domain)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def supersede(self, old_id: uuid.UUID, new_id: uuid.UUID) -> None:
        await self.session.execute(
            update(MemoryFact).where(MemoryFact.id == old_id).values(active=False, superseded_by=new_id)
        )


class SemanticMemoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, memory: SemanticMemory) -> SemanticMemory:
        self.session.add(memory)
        await self.session.flush()
        return memory

    async def search_by_embedding(
        self,
        embedding: list[float],
        limit: int = 10,
        domain: str | None = None,
    ) -> list[SemanticMemory]:
        """Semantic search using pgvector cosine distance."""
        stmt = (
            select(SemanticMemory)
            .where(
                SemanticMemory.deleted_at.is_(None),
                SemanticMemory.embedding.isnot(None),
            )
            .order_by(SemanticMemory.embedding.cosine_distance(embedding))
            .limit(limit)
        )
        if domain is not None:
            stmt = stmt.where(SemanticMemory.source_domain == domain)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def increment_access(self, memory_id: uuid.UUID) -> None:
        await self.session.execute(
            update(SemanticMemory)
            .where(SemanticMemory.id == memory_id)
            .values(
                access_count=SemanticMemory.access_count + 1,
                last_accessed_at=datetime.utcnow(),
            )
        )


class ConversationSummaryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, summary: ConversationSummary) -> ConversationSummary:
        self.session.add(summary)
        await self.session.flush()
        return summary

    async def list_recent(self, limit: int = 10) -> list[ConversationSummary]:
        result = await self.session.execute(
            select(ConversationSummary).order_by(ConversationSummary.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
