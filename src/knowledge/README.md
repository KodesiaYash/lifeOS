# Knowledge Module (`src/knowledge/`)

Knowledge ingestion, storage, and retrieval for documents, articles, notes, and other content.

## Contents

| File | Purpose |
|------|---------|
| `models.py` | SQLAlchemy models: KnowledgeDocument, KnowledgeChunk (with pgvector), KnowledgeRelation |
| `schemas.py` | Pydantic schemas for document creation and reading |
| `repository.py` | Database access including pgvector similarity search on chunks |
| `ingestion.py` | `IngestionPipeline` — full pipeline: fetch → parse → dedup → chunk → embed → store |
| `chunking.py` | `TextChunker` — recursive character text splitter with overlap |
| `embedding.py` | `EmbeddingService` — OpenAI text-embedding-3-small wrapper |
| `tagging.py` | `TaggingService` — LLM-based auto-tagging and entity extraction (stub) |
| `parsers/html.py` | HTML/web page parser (stub) |
| `parsers/pdf.py` | PDF parser (stub) |
| `parsers/document.py` | Office document parser (stub) |
| `parsers/youtube.py` | YouTube transcript parser (stub) |

## Ingestion Pipeline

1. Create document record (status=pending)
2. Fetch raw content (via parser for the source type)
3. Deduplication check (SHA-256 content hash)
4. Chunk text (recursive character splitter, 512 tokens, 64 overlap)
5. Generate embeddings (batch)
6. Store chunks with embeddings
7. Auto-tag and classify (LLM-based)
8. Update document status → completed
