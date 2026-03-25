"""
Unit tests for src/retrieval/schemas.py — retrieval request/response schemas.

Tests:
  - test_request_defaults: Default strategy is HYBRID, max_results=20, min_relevance=0.3
  - test_request_custom_strategy: Can override strategy to SEMANTIC/STRUCTURED/KEYWORD
  - test_result_creation: RetrievalResult with all fields
  - test_result_optional_domain: Domain is optional
  - test_strategy_enum_values: All expected strategies exist
"""
import uuid

from src.retrieval.schemas import RetrievalRequest, RetrievalResult, RetrievalStrategy


class TestRetrievalRequest:
    """Verify retrieval request schema defaults and overrides."""

    def test_request_defaults(self):
        """Default: hybrid strategy, 20 results, 0.3 min score."""
        req = RetrievalRequest(
            tenant_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            query="test query",
        )
        assert req.strategy == RetrievalStrategy.HYBRID
        assert req.max_results == 20
        assert req.min_relevance_score == 0.3

    def test_request_custom_strategy(self):
        """Can specify SEMANTIC-only retrieval."""
        req = RetrievalRequest(
            tenant_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            query="test",
            strategy=RetrievalStrategy.SEMANTIC,
        )
        assert req.strategy == RetrievalStrategy.SEMANTIC


class TestRetrievalResult:
    """Verify retrieval result schema."""

    def test_result_creation(self):
        """All fields are preserved."""
        r = RetrievalResult(
            id=uuid.uuid4(),
            source="knowledge_chunk",
            content="Some content",
            relevance_score=0.85,
            domain="health",
        )
        assert r.source == "knowledge_chunk"
        assert r.relevance_score == 0.85
        assert r.domain == "health"

    def test_result_optional_domain(self):
        """Domain is optional."""
        r = RetrievalResult(
            id=uuid.uuid4(),
            source="memory",
            content="content",
            relevance_score=0.5,
        )
        assert r.domain is None


class TestRetrievalStrategy:
    """Verify strategy enum members."""

    def test_strategy_enum_values(self):
        """All four strategies exist."""
        assert RetrievalStrategy.SEMANTIC == "semantic"
        assert RetrievalStrategy.STRUCTURED == "structured"
        assert RetrievalStrategy.KEYWORD == "keyword"
        assert RetrievalStrategy.HYBRID == "hybrid"
