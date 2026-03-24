"""
Retrieval coordinator: routes requests to the appropriate retrievers,
fuses results, and returns a unified RetrievalResponse.
"""
import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.knowledge.embedding import EmbeddingService
from src.retrieval.keyword_retriever import KeywordRetriever
from src.retrieval.reranker import Reranker
from src.retrieval.schemas import RetrievalRequest, RetrievalResponse, RetrievalResult, RetrievalStrategy
from src.retrieval.semantic_retriever import SemanticRetriever
from src.retrieval.structured_retriever import StructuredRetriever

logger = structlog.get_logger()


class RetrievalCoordinator:
    """
    Orchestrates retrieval across all sources based on strategy.
    Generates embeddings on-demand, routes to retrievers, fuses and reranks.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.semantic = SemanticRetriever(session)
        self.structured = StructuredRetriever(session)
        self.keyword = KeywordRetriever(session)
        self.reranker = Reranker()
        self.embedding_service = EmbeddingService()

    async def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        """Execute a retrieval request according to the specified strategy."""
        # Compute embedding if needed and not provided
        embedding = request.query_embedding
        needs_embedding = request.strategy in (
            RetrievalStrategy.SEMANTIC,
            RetrievalStrategy.HYBRID,
            RetrievalStrategy.ALL,
            RetrievalStrategy.MEMORY_ONLY,
            RetrievalStrategy.KNOWLEDGE_ONLY,
        )
        if needs_embedding and embedding is None:
            embedding = await self.embedding_service.embed_text(request.query)

        all_results: list[RetrievalResult] = []
        domain = request.domains[0] if request.domains and len(request.domains) == 1 else None

        # Route to retrievers based on strategy
        if request.strategy in (RetrievalStrategy.STRUCTURED, RetrievalStrategy.HYBRID, RetrievalStrategy.ALL):
            structured_results = await self.structured.search(
                tenant_id=request.tenant_id,
                user_id=request.user_id,
                query=request.query,
                domain=domain,
                max_results=request.max_results,
            )
            all_results.extend(structured_results)

        if request.strategy in (
            RetrievalStrategy.SEMANTIC, RetrievalStrategy.HYBRID, RetrievalStrategy.ALL,
            RetrievalStrategy.MEMORY_ONLY, RetrievalStrategy.KNOWLEDGE_ONLY,
        ) and embedding:
            search_memories = request.strategy not in (RetrievalStrategy.KNOWLEDGE_ONLY,)
            search_knowledge = request.strategy not in (RetrievalStrategy.MEMORY_ONLY,)
            semantic_results = await self.semantic.search(
                tenant_id=request.tenant_id,
                user_id=request.user_id,
                query_embedding=embedding,
                max_results=request.max_results,
                domain=domain,
                search_memories=search_memories,
                search_knowledge=search_knowledge,
            )
            all_results.extend(semantic_results)

        if request.strategy in (RetrievalStrategy.KEYWORD, RetrievalStrategy.HYBRID, RetrievalStrategy.ALL):
            keyword_results = await self.keyword.search(
                tenant_id=request.tenant_id,
                user_id=request.user_id,
                query=request.query,
                max_results=request.max_results,
            )
            all_results.extend(keyword_results)

        # Deduplicate by content (same chunk from different retrievers)
        all_results = self._deduplicate(all_results)

        # Rerank
        ranked = self.reranker.rerank(
            results=all_results,
            recency_weight=request.recency_weight,
            importance_weight=request.importance_weight,
            diversity_factor=request.diversity_factor,
            min_score=request.min_relevance_score,
        )

        # Limit to max_results
        ranked = ranked[:request.max_results]

        logger.info(
            "retrieval_complete",
            strategy=request.strategy,
            query_preview=request.query[:50],
            total_found=len(all_results),
            returned=len(ranked),
        )

        return RetrievalResponse(
            results=ranked,
            total_found=len(all_results),
            strategy_used=request.strategy,
            query=request.query,
        )

    def _deduplicate(self, results: list[RetrievalResult]) -> list[RetrievalResult]:
        """Remove duplicate results (same ID from multiple retrievers)."""
        seen_ids: set[uuid.UUID] = set()
        deduped: list[RetrievalResult] = []
        for r in results:
            if r.id not in seen_ids:
                seen_ids.add(r.id)
                deduped.append(r)
        return deduped
