"""
Long-term structured memory: SQL-backed fact store.
Stores discrete, queryable facts about the user (preferences, goals, habits, etc.).
"""
import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.memory.models import MemoryFact
from src.memory.repository import MemoryFactRepository
from src.memory.schemas import MemoryFactCreate

logger = structlog.get_logger()


class StructuredMemory:
    """
    SQL-backed structured memory layer.
    Stores key-value facts with categories, domains, and confidence scores.
    Supports fact supersession (updating a fact creates a new version).
    """

    def __init__(self, session: AsyncSession) -> None:
        self.repo = MemoryFactRepository(session)

    async def remember(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        data: MemoryFactCreate,
    ) -> MemoryFact:
        """
        Store a fact. If a fact with the same key already exists,
        supersede it with the new value.
        """
        existing = await self.repo.get_by_key(tenant_id, user_id, data.key)

        fact = MemoryFact(
            tenant_id=tenant_id,
            user_id=user_id,
            domain=data.domain,
            category=data.category,
            key=data.key,
            value=data.value,
            structured_value=data.structured_value,
            confidence=data.confidence,
            source=data.source,
        )
        fact = await self.repo.create(fact)

        if existing is not None:
            await self.repo.supersede(existing.id, fact.id)
            logger.info("fact_superseded", key=data.key, old_id=str(existing.id), new_id=str(fact.id))
        else:
            logger.info("fact_stored", key=data.key, category=data.category)

        return fact

    async def recall(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        key: str,
    ) -> MemoryFact | None:
        """Recall a specific fact by key."""
        return await self.repo.get_by_key(tenant_id, user_id, key)

    async def recall_by_category(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        category: str,
        domain: str | None = None,
    ) -> list[MemoryFact]:
        """Recall all facts in a category."""
        return await self.repo.list_by_category(tenant_id, user_id, category, domain)

    async def recall_all(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        domain: str | None = None,
    ) -> list[MemoryFact]:
        """Recall all active facts for a user."""
        return await self.repo.list_all_active(tenant_id, user_id, domain)
