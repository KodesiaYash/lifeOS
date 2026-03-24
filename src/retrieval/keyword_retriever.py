"""
Keyword retriever: PostgreSQL full-text search (tsvector/tsquery).
"""
import uuid

import structlog
from sqlalchemy import text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession

from src.retrieval.schemas import RetrievalResult

logger = structlog.get_logger()


class KeywordRetriever:
    """Searches knowledge chunks and documents using PostgreSQL full-text search."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def search(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        query: str,
        max_results: int = 10,
    ) -> list[RetrievalResult]:
        """
        Full-text search on knowledge chunks using tsquery.
        Returns results ranked by ts_rank.
        """
        # Convert query to tsquery format (simple word-level AND)
        words = query.strip().split()
        if not words:
            return []
        tsquery = " & ".join(words)

        stmt = sql_text("""
            SELECT
                kc.id,
                kc.text,
                kc.document_id,
                kc.chunk_index,
                kc.created_at,
                ts_rank(to_tsvector('english', kc.text), to_tsquery('english', :tsquery)) AS rank
            FROM know_chunks kc
            WHERE kc.tenant_id = :tenant_id
              AND kc.user_id = :user_id
              AND kc.deleted_at IS NULL
              AND to_tsvector('english', kc.text) @@ to_tsquery('english', :tsquery)
            ORDER BY rank DESC
            LIMIT :limit
        """)

        result = await self.session.execute(
            stmt,
            {
                "tenant_id": str(tenant_id),
                "user_id": str(user_id),
                "tsquery": tsquery,
                "limit": max_results,
            },
        )
        rows = result.fetchall()

        results: list[RetrievalResult] = []
        for row in rows:
            results.append(RetrievalResult(
                id=row.id,
                source="knowledge_chunk_fts",
                content=row.text,
                relevance_score=float(row.rank),
                created_at=row.created_at,
                metadata={
                    "document_id": str(row.document_id),
                    "chunk_index": row.chunk_index,
                    "search_type": "full_text",
                },
            ))

        logger.debug("keyword_search_complete", query=query, results=len(results))
        return results
