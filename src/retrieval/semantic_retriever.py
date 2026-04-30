"""
Semantic retriever: pgvector cosine similarity search across memories and knowledge.

Single-user mode: No tenant_id or user_id needed.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.knowledge.repository import KnowledgeChunkRepository
from src.memory.repository import SemanticMemoryRepository
from src.retrieval.schemas import RetrievalResult

logger = structlog.get_logger()


class SemanticRetriever:
    """Searches semantic memories and knowledge chunks via embedding similarity."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.semantic_repo = SemanticMemoryRepository(session)
        self.chunk_repo = KnowledgeChunkRepository(session)

    async def search(
        self,
        query_embedding: list[float],
        max_results: int = 10,
        domain: str | None = None,
        domains: list[str] | None = None,
        search_memories: bool = True,
        search_knowledge: bool = True,
    ) -> list[RetrievalResult]:
        """Search both semantic memories and knowledge chunks."""
        results: list[RetrievalResult] = []

        if search_memories:
            memories = await self.semantic_repo.search_by_embedding(
                embedding=query_embedding,
                limit=max_results,
                domain=domain,
                domains=domains,
            )
            for mem in memories:
                results.append(
                    RetrievalResult(
                        id=mem.id,
                        source="semantic_memory",
                        content=mem.content,
                        relevance_score=0.0,  # Will be scored by reranker
                        domain=mem.source_domain,
                        created_at=mem.created_at,
                        metadata={"memory_type": mem.memory_type, "importance": mem.importance},
                    )
                )

        if search_knowledge:
            chunks = await self.chunk_repo.search_by_embedding(
                embedding=query_embedding,
                limit=max_results,
            )
            for chunk in chunks:
                results.append(
                        RetrievalResult(
                            id=chunk.id,
                            source="knowledge_chunk",
                            content=chunk.content,
                            relevance_score=0.0,
                            created_at=chunk.created_at,
                        metadata={"document_id": str(chunk.document_id), "chunk_index": chunk.chunk_index},
                    )
                )

        logger.debug("semantic_search_complete", results=len(results))
        return results
