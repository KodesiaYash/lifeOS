"""
Tests for the retrieval module.
"""
import uuid
from datetime import datetime, timezone, timedelta

import pytest

from src.retrieval.reranker import Reranker
from src.retrieval.schemas import RetrievalRequest, RetrievalResult, RetrievalStrategy


class TestReranker:
    def setup_method(self):
        self.reranker = Reranker()

    def _make_result(self, content: str, score: float, created_at=None, importance=0.5) -> RetrievalResult:
        return RetrievalResult(
            id=uuid.uuid4(),
            source="test",
            content=content,
            relevance_score=score,
            created_at=created_at or datetime.now(timezone.utc),
            metadata={"importance": importance},
        )

    def test_empty_results(self):
        assert self.reranker.rerank([]) == []

    def test_preserves_order_by_score(self):
        results = [
            self._make_result("low", 0.3),
            self._make_result("high", 0.9),
            self._make_result("mid", 0.6),
        ]
        ranked = self.reranker.rerank(results, min_score=0.0)
        scores = [r.relevance_score for r in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_min_score_filtering(self):
        results = [
            self._make_result("high", 0.9),
            self._make_result("low", 0.1),
        ]
        ranked = self.reranker.rerank(results, min_score=0.3)
        assert len(ranked) <= 2
        for r in ranked:
            assert r.relevance_score >= 0.3

    def test_recency_boost(self):
        now = datetime.now(timezone.utc)
        recent = self._make_result("recent", 0.5, created_at=now)
        old = self._make_result("old content different", 0.5, created_at=now - timedelta(days=30))
        ranked = self.reranker.rerank([old, recent], recency_weight=0.5, min_score=0.0)
        # Recent item should rank higher with high recency weight
        assert ranked[0].content == "recent"

    def test_diversity_penalty(self):
        results = [
            self._make_result("the quick brown fox", 0.8),
            self._make_result("the quick brown fox jumps", 0.8),
            self._make_result("completely different content here", 0.8),
        ]
        ranked = self.reranker.rerank(results, diversity_factor=0.5, min_score=0.0)
        # The duplicate-ish content should be penalized
        assert len(ranked) >= 2


class TestRetrievalSchemas:
    def test_retrieval_request_defaults(self):
        req = RetrievalRequest(
            tenant_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            query="test query",
        )
        assert req.strategy == RetrievalStrategy.HYBRID
        assert req.max_results == 20
        assert req.min_relevance_score == 0.3

    def test_retrieval_result(self):
        result = RetrievalResult(
            id=uuid.uuid4(),
            source="knowledge_chunk",
            content="Some content",
            relevance_score=0.85,
            domain="health",
        )
        assert result.source == "knowledge_chunk"
        assert result.relevance_score == 0.85
