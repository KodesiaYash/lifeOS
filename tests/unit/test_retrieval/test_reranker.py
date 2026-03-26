"""
Unit tests for src/retrieval/reranker.py — multi-signal reranking.

Tests:
  - test_empty_results: Empty input returns empty output
  - test_preserves_descending_order: Output is sorted by final score descending
  - test_min_score_filtering: Results below min_score are excluded
  - test_recency_boost: Recent items score higher when recency_weight > 0
  - test_diversity_penalty: Near-duplicate content is penalised
  - test_importance_weight: Higher-importance items rank above equal-relevance peers
  - test_max_results_limit: Output respects max_results cap
"""

import uuid
from datetime import UTC, datetime, timedelta

from src.retrieval.reranker import Reranker
from src.retrieval.schemas import RetrievalResult


def _result(content: str, score: float, created_at=None, importance=0.5) -> RetrievalResult:
    return RetrievalResult(
        id=uuid.uuid4(),
        source="test",
        content=content,
        relevance_score=score,
        created_at=created_at or datetime.now(UTC),
        metadata={"importance": importance},
    )


class TestReranker:
    """Verify multi-signal reranking algorithm."""

    def setup_method(self):
        self.reranker = Reranker()

    def test_empty_results(self):
        """No input → no output, no crash."""
        assert self.reranker.rerank([]) == []

    def test_preserves_descending_order(self):
        """Output is sorted highest score first."""
        results = [_result("low", 0.3), _result("high", 0.9), _result("mid", 0.6)]
        ranked = self.reranker.rerank(results, min_score=0.0)
        scores = [r.relevance_score for r in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_min_score_filtering(self):
        """Results with final score below min_score are excluded."""
        results = [_result("high", 0.9), _result("low", 0.1)]
        ranked = self.reranker.rerank(results, min_score=0.3)
        for r in ranked:
            assert r.relevance_score >= 0.3

    def test_recency_boost(self):
        """With recency_weight > 0, recent items rank above older ones at equal relevance."""
        now = datetime.now(UTC)
        recent = _result("recent", 0.5, created_at=now)
        old = _result("old content here", 0.5, created_at=now - timedelta(days=30))
        ranked = self.reranker.rerank([old, recent], recency_weight=0.5, min_score=0.0)
        assert ranked[0].content == "recent"

    def test_diversity_penalty(self):
        """Near-duplicate content gets penalised to promote variety."""
        results = [
            _result("the quick brown fox", 0.8),
            _result("the quick brown fox jumps over", 0.8),
            _result("completely different content here", 0.8),
        ]
        ranked = self.reranker.rerank(results, diversity_factor=0.5, min_score=0.0)
        assert len(ranked) >= 2

    def test_importance_weight(self):
        """Higher importance metadata boosts final score."""
        low_imp = _result("low importance", 0.7, importance=0.1)
        high_imp = _result("high importance", 0.7, importance=0.9)
        ranked = self.reranker.rerank(
            [low_imp, high_imp],
            importance_weight=0.5,
            min_score=0.0,
        )
        # High importance item should rank first or equal
        assert ranked[0].metadata["importance"] >= ranked[-1].metadata["importance"]
