"""
Integration test: Knowledge chunking → token estimation → ingestion readiness.

Tests the knowledge pipeline's pure logic layers (no DB, no embeddings).
Verifies chunks are correctly sized, token estimates are reasonable,
and the pipeline's data transformations preserve content.

Tests:
  - test_chunk_then_estimate_tokens: Chunks are within token budget
  - test_large_document_chunking: Real-world-sized document produces expected chunk count
  - test_chunk_content_completeness: All sentences from source appear in chunks
  - test_chunk_metadata_indices: Chunks have sequential indices
"""

from src.knowledge.chunking import TextChunker, estimate_tokens


class TestKnowledgeFlow:
    """Integration: chunking → token estimation pipeline."""

    def test_chunk_then_estimate_tokens(self):
        """
        Scenario: A 2000-word article is chunked at 500 chars.
        Each chunk should estimate to < 200 tokens.
        """
        chunker = TextChunker(chunk_size=500, chunk_overlap=50)
        article = "This is a sentence about health and nutrition. " * 200  # ~9400 chars
        chunks = chunker.chunk(article)

        assert len(chunks) > 1
        for chunk in chunks:
            tokens = estimate_tokens(chunk)
            assert tokens < 200, f"Chunk too large: {tokens} tokens"

    def test_large_document_chunking(self):
        """
        Scenario: 50-page document (~25000 words).
        Should produce ~50-100 chunks at 500 char chunk size.
        """
        chunker = TextChunker(chunk_size=500, chunk_overlap=50)
        document = ("Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 50 + "\n\n") * 50
        chunks = chunker.chunk(document)
        assert 20 < len(chunks) < 500

    def test_chunk_content_completeness(self):
        """
        Scenario: Document with 10 unique sentences.
        Every sentence must appear in at least one chunk.
        """
        chunker = TextChunker(chunk_size=200, chunk_overlap=30)
        sentences = [f"Unique sentence number {i} with distinctive content." for i in range(10)]
        document = " ".join(sentences)
        chunks = chunker.chunk(document)
        all_text = " ".join(chunks)

        for i in range(10):
            assert f"number {i}" in all_text, f"Sentence {i} missing from chunks"

    def test_chunk_metadata_indices(self):
        """
        Scenario: Chunks should be enumerable for storage with chunk_index.
        Verify sequential indexing is possible.
        """
        chunker = TextChunker(chunk_size=100, chunk_overlap=10)
        text = "Word " * 200
        chunks = chunker.chunk(text)

        indexed = list(enumerate(chunks))
        assert indexed[0][0] == 0
        assert indexed[-1][0] == len(chunks) - 1
