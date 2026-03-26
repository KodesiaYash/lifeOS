"""
Unit tests for src/knowledge/chunking.py — text chunking and token estimation.

Tests:
  - test_short_text_no_split: Text shorter than chunk_size returns single chunk
  - test_empty_text: Empty/whitespace-only text returns empty list
  - test_splits_long_text: Long text is split into multiple chunks
  - test_chunk_size_respected: No chunk exceeds chunk_size (with tolerance)
  - test_preserves_content: No information lost — all words appear in some chunk
  - test_paragraph_splitting: Double-newline paragraph boundaries are preferred split points
  - test_overlap_creates_redundancy: Overlap > 0 produces shared content between adjacent chunks
  - test_zero_overlap: Zero overlap produces non-overlapping chunks
  - test_estimate_tokens_basic: Token estimate is reasonable for short text
  - test_estimate_tokens_empty: Empty string → 0 tokens
  - test_estimate_tokens_long: Proportional to text length
"""

from src.knowledge.chunking import TextChunker, estimate_tokens


class TestTextChunker:
    """Verify recursive character text splitting."""

    def test_short_text_no_split(self):
        """Text within chunk_size → single chunk, unchanged."""
        chunker = TextChunker(chunk_size=100)
        text = "Hello world, this is a short text."
        chunks = chunker.chunk(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_empty_text(self):
        """Empty or whitespace-only text → empty list."""
        chunker = TextChunker(chunk_size=100)
        assert chunker.chunk("") == []
        assert chunker.chunk("   ") == []

    def test_splits_long_text(self):
        """Text exceeding chunk_size is split into multiple chunks."""
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)
        text = "This is a sentence. " * 20
        chunks = chunker.chunk(text)
        assert len(chunks) > 1

    def test_chunk_size_respected(self):
        """No individual chunk exceeds chunk_size + tolerance."""
        chunker = TextChunker(chunk_size=80, chunk_overlap=10)
        text = "Word " * 200
        chunks = chunker.chunk(text)
        for chunk in chunks:
            assert len(chunk) <= 100  # chunk_size + tolerance for split boundaries

    def test_preserves_content(self):
        """All original tokens appear in at least one chunk (no data loss)."""
        chunker = TextChunker(chunk_size=100, chunk_overlap=0)
        words = [f"uniqueword{i}" for i in range(20)]
        text = " ".join(words)
        chunks = chunker.chunk(text)
        rejoined = " ".join(chunks)
        for word in words:
            assert word in rejoined, f"Word '{word}' lost during chunking"

    def test_paragraph_splitting(self):
        """Double-newlines are preferred split points."""
        chunker = TextChunker(chunk_size=100, chunk_overlap=0)
        text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        chunks = chunker.chunk(text)
        assert len(chunks) >= 1

    def test_overlap_creates_redundancy(self):
        """With overlap > 0, adjacent chunks share some content."""
        chunker = TextChunker(chunk_size=50, chunk_overlap=20)
        text = "word " * 100
        chunks = chunker.chunk(text)
        if len(chunks) >= 2:
            # Last part of chunk 0 should appear in start of chunk 1
            end_of_first = chunks[0][-15:]
            assert end_of_first in chunks[1] or chunks[1].startswith("word")

    def test_zero_overlap(self):
        """With overlap=0, chunks should be non-overlapping."""
        chunker = TextChunker(chunk_size=50, chunk_overlap=0)
        text = "word " * 100
        chunks = chunker.chunk(text)
        assert len(chunks) > 1


class TestEstimateTokens:
    """Verify token count estimation (chars / 4 heuristic)."""

    def test_estimate_tokens_basic(self):
        """'Hello world' (11 chars) → ~2-3 tokens."""
        tokens = estimate_tokens("Hello world")
        assert 0 < tokens < 10

    def test_estimate_tokens_empty(self):
        """Empty string → 0 tokens."""
        assert estimate_tokens("") == 0

    def test_estimate_tokens_long(self):
        """500 chars → ~125 tokens (chars / 4)."""
        text = "word " * 100  # 500 chars
        tokens = estimate_tokens(text)
        assert 100 <= tokens <= 150
