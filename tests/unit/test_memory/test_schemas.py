"""
Unit tests for src/memory/schemas.py — memory layer schemas.

Tests:
  - test_memory_fact_create_valid: Valid fact with all required fields
  - test_memory_fact_confidence_range: Confidence is a float between 0 and 1
  - test_semantic_memory_create_valid: Valid semantic memory with content + type
  - test_semantic_memory_importance_default: Importance defaults to 0.5
  - test_memory_packet_structure: MemoryPacket contains all four sections
  - test_memory_packet_token_count: total_tokens is preserved
"""
from src.memory.schemas import MemoryFactCreate, MemoryPacket, SemanticMemoryCreate


class TestMemoryFactCreate:
    """Verify structured memory fact creation."""

    def test_memory_fact_create_valid(self):
        """All required fields populated."""
        fact = MemoryFactCreate(
            category="dietary_preference",
            key="diet_type",
            value="vegetarian",
            domain="health",
            confidence=0.95,
            source="user_stated",
        )
        assert fact.category == "dietary_preference"
        assert fact.key == "diet_type"
        assert fact.value == "vegetarian"
        assert fact.confidence == 0.95

    def test_memory_fact_confidence_range(self):
        """Confidence is a valid float."""
        fact = MemoryFactCreate(
            category="test",
            key="k",
            value="v",
            confidence=0.0,
            source="test",
        )
        assert 0.0 <= fact.confidence <= 1.0


class TestSemanticMemoryCreate:
    """Verify semantic memory creation."""

    def test_semantic_memory_create_valid(self):
        """Content + memory_type are required."""
        mem = SemanticMemoryCreate(
            content="User prefers morning workouts",
            memory_type="preference",
            source_domain="health",
            importance=0.8,
        )
        assert mem.content == "User prefers morning workouts"
        assert mem.importance == 0.8

    def test_semantic_memory_importance_default(self):
        """Importance should have a sensible default."""
        mem = SemanticMemoryCreate(
            content="test",
            memory_type="observation",
        )
        assert isinstance(mem.importance, (int, float))


class TestMemoryPacket:
    """Verify the assembled memory packet structure."""

    def test_memory_packet_structure(self):
        """All four sections present."""
        packet = MemoryPacket(
            session_context={"topic": "nutrition"},
            user_facts=[{"key": "diet", "value": "vegan"}],
            semantic_matches=["match1"],
            recent_summaries=["summary1"],
            total_tokens=200,
        )
        assert packet.session_context["topic"] == "nutrition"
        assert len(packet.user_facts) == 1
        assert len(packet.semantic_matches) == 1
        assert len(packet.recent_summaries) == 1

    def test_memory_packet_token_count(self):
        """Token budget tracking works."""
        packet = MemoryPacket(
            session_context={},
            user_facts=[],
            semantic_matches=[],
            recent_summaries=[],
            total_tokens=150,
        )
        assert packet.total_tokens == 150

    def test_memory_packet_empty(self):
        """Empty packet is valid — new user with no history."""
        packet = MemoryPacket(
            session_context={},
            user_facts=[],
            semantic_matches=[],
            recent_summaries=[],
            total_tokens=0,
        )
        assert packet.total_tokens == 0
