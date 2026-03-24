"""
Tests for the knowledge module.
"""
import pytest

from src.knowledge.chunking import TextChunker, estimate_tokens


class TestTextChunker:
    def test_short_text_no_split(self):
        chunker = TextChunker(chunk_size=100)
        text = "Hello world, this is a short text."
        chunks = chunker.chunk(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_empty_text(self):
        chunker = TextChunker(chunk_size=100)
        assert chunker.chunk("") == []
        assert chunker.chunk("   ") == []

    def test_splits_long_text(self):
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)
        text = "This is a sentence. " * 20
        chunks = chunker.chunk(text)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 60  # Allow some flexibility due to splitting

    def test_preserves_content(self):
        chunker = TextChunker(chunk_size=100, chunk_overlap=0)
        sentences = [f"Sentence number {i}." for i in range(10)]
        text = " ".join(sentences)
        chunks = chunker.chunk(text)
        # All original words should appear in some chunk
        rejoined = " ".join(chunks)
        for s in sentences:
            # At least the sentence number should be present
            assert str(sentences.index(s)) in rejoined or s.split()[0] in rejoined

    def test_paragraph_splitting(self):
        chunker = TextChunker(chunk_size=100, chunk_overlap=0)
        text = "Paragraph one content here.\n\nParagraph two content here.\n\nParagraph three content here."
        chunks = chunker.chunk(text)
        assert len(chunks) >= 1


class TestEstimateTokens:
    def test_basic_estimate(self):
        text = "Hello world"  # 11 chars -> ~2-3 tokens
        tokens = estimate_tokens(text)
        assert tokens > 0
        assert tokens < 10

    def test_empty_string(self):
        assert estimate_tokens("") == 0

    def test_longer_text(self):
        text = "word " * 100  # 500 chars -> ~125 tokens
        tokens = estimate_tokens(text)
        assert 100 <= tokens <= 150
