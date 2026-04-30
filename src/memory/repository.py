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

    async def get_by_id(self, fact_id: uuid.UUID) -> MemoryFact | None:
        result = await self.session.execute(select(MemoryFact).where(MemoryFact.id == fact_id))
        return result.scalar_one_or_none()

    async def get_by_key(self, key: str, domain: str | None = None) -> MemoryFact | None:
        stmt = select(MemoryFact).where(
            MemoryFact.key == key,
            MemoryFact.active.is_(True),
        )
        if domain is None:
            stmt = stmt.where(MemoryFact.domain.is_(None))
        else:
            stmt = stmt.where(MemoryFact.domain == domain)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_category(
        self,
        category: str,
        domain: str | None = None,
        domains: list[str] | None = None,
    ) -> list[MemoryFact]:
        stmt = select(MemoryFact).where(
            MemoryFact.category == category,
            MemoryFact.active.is_(True),
        )
        if domains:
            stmt = stmt.where(MemoryFact.domain.in_(domains))
        elif domain is not None:
            stmt = stmt.where(MemoryFact.domain == domain)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all_active(
        self,
        domain: str | None = None,
        domains: list[str] | None = None,
    ) -> list[MemoryFact]:
        stmt = select(MemoryFact).where(MemoryFact.active.is_(True))
        if domains:
            stmt = stmt.where(MemoryFact.domain.in_(domains))
        elif domain is not None:
            stmt = stmt.where(MemoryFact.domain == domain)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def supersede(self, old_id: uuid.UUID, new_id: uuid.UUID) -> None:
        await self.session.execute(
            update(MemoryFact).where(MemoryFact.id == old_id).values(active=False, superseded_by=new_id)
        )

    async def deactivate(self, fact_id: uuid.UUID) -> MemoryFact | None:
        fact = await self.get_by_id(fact_id)
        if fact is None:
            return None
        fact.active = False
        fact.deleted_at = datetime.utcnow()
        await self.session.flush()
        return fact


class SemanticMemoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, memory: SemanticMemory) -> SemanticMemory:
        self.session.add(memory)
        await self.session.flush()
        return memory

    async def get_by_id(self, memory_id: uuid.UUID) -> SemanticMemory | None:
        result = await self.session.execute(select(SemanticMemory).where(SemanticMemory.id == memory_id))
        return result.scalar_one_or_none()

    async def list_all(
        self,
        domain: str | None = None,
        domains: list[str] | None = None,
        limit: int = 50,
    ) -> list[SemanticMemory]:
        stmt = select(SemanticMemory).where(SemanticMemory.deleted_at.is_(None)).order_by(SemanticMemory.created_at.desc())
        if domains:
            stmt = stmt.where(SemanticMemory.source_domain.in_(domains))
        elif domain is not None:
            stmt = stmt.where(SemanticMemory.source_domain == domain)
        result = await self.session.execute(stmt.limit(limit))
        return list(result.scalars().all())

    async def search_by_embedding(
        self,
        embedding: list[float],
        limit: int = 10,
        domain: str | None = None,
        domains: list[str] | None = None,
    ) -> list[SemanticMemory]:
        """Semantic search using pgvector cosine distance."""
        stmt = select(SemanticMemory).where(
            SemanticMemory.deleted_at.is_(None),
            SemanticMemory.embedding.isnot(None),
        )
        if domains:
            stmt = stmt.where(SemanticMemory.source_domain.in_(domains))
        elif domain is not None:
            stmt = stmt.where(SemanticMemory.source_domain == domain)

        if hasattr(SemanticMemory.embedding, "cosine_distance"):
            stmt = stmt.order_by(SemanticMemory.embedding.cosine_distance(embedding))
        else:
            stmt = stmt.order_by(SemanticMemory.importance.desc(), SemanticMemory.created_at.desc())

        stmt = stmt.limit(limit)
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

    async def soft_delete(self, memory_id: uuid.UUID) -> SemanticMemory | None:
        memory = await self.get_by_id(memory_id)
        if memory is None:
            return None
        memory.deleted_at = datetime.utcnow()
        await self.session.flush()
        return memory


class ConversationSummaryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, summary: ConversationSummary) -> ConversationSummary:
        self.session.add(summary)
        await self.session.flush()
        return summary

    async def list_recent(self, limit: int = 10, domains: list[str] | None = None) -> list[ConversationSummary]:
        result = await self.session.execute(
            select(ConversationSummary).order_by(ConversationSummary.created_at.desc()).limit(max(limit * 3, limit))
        )
        summaries = list(result.scalars().all())
        if not domains:
            return summaries[:limit]

        filtered = [
            summary
            for summary in summaries
            if set(summary.domains_involved or []).intersection(domains)
        ]
        return filtered[:limit]
