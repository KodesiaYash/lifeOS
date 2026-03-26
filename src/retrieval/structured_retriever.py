"""
Structured retriever: SQL-based retrieval for facts, entities, and structured data.

Single-user mode: No tenant_id or user_id needed.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.memory.repository import MemoryFactRepository
from src.retrieval.schemas import RetrievalResult

logger = structlog.get_logger()


class StructuredRetriever:
    """Searches structured memory facts and entities via SQL queries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.fact_repo = MemoryFactRepository(session)

    async def search(
        self,
        query: str,
        domain: str | None = None,
        category: str | None = None,
        max_results: int = 20,
    ) -> list[RetrievalResult]:
        """
        Search structured facts by category and domain.
        Also performs simple keyword matching on fact keys and values.
        """
        if category:
            facts = await self.fact_repo.list_by_category(category, domain)
        else:
            facts = await self.fact_repo.list_all_active(domain)

        results: list[RetrievalResult] = []
        query_lower = query.lower()

        for fact in facts[:max_results]:
            # Simple keyword relevance scoring
            score = 0.0
            if query_lower in fact.key.lower():
                score = 0.8
            elif query_lower in fact.value.lower():
                score = 0.6
            elif fact.category.lower() in query_lower:
                score = 0.4
            else:
                score = 0.2  # Base score for all active facts

            results.append(
                RetrievalResult(
                    id=fact.id,
                    source="memory_fact",
                    content=f"{fact.key}: {fact.value}",
                    relevance_score=score,
                    domain=fact.domain,
                    created_at=fact.created_at,
                    metadata={
                        "category": fact.category,
                        "confidence": fact.confidence,
                        "source": fact.source,
                    },
                )
            )

        results.sort(key=lambda r: r.relevance_score, reverse=True)
        logger.debug("structured_search_complete", results=len(results))
        return results
