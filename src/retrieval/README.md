# Retrieval Module (`src/retrieval/`)

Hybrid RAG retrieval layer: semantic, structured, and keyword search with multi-signal reranking.

## Contents

| File | Purpose |
|------|---------|
| `schemas.py` | `RetrievalRequest`, `RetrievalResult`, `RetrievalResponse`, `RetrievalStrategy` enum |
| `coordinator.py` | `RetrievalCoordinator` — routes to retrievers, fuses, deduplicates, reranks |
| `semantic_retriever.py` | pgvector cosine similarity search on memories and knowledge chunks |
| `structured_retriever.py` | SQL-based retrieval for memory facts with keyword scoring |
| `keyword_retriever.py` | PostgreSQL full-text search (tsvector/tsquery) on knowledge chunks |
| `reranker.py` | Multi-signal reranking: relevance, recency, importance, diversity |

## Strategies

| Strategy | Retrievers Used |
|----------|----------------|
| `structured` | StructuredRetriever only |
| `semantic` | SemanticRetriever only |
| `keyword` | KeywordRetriever only |
| `hybrid` | All three (default) |
| `memory_only` | SemanticRetriever (memories only) |
| `knowledge_only` | SemanticRetriever (knowledge only) |
| `all` | All retrievers, all sources |

## Reranking

Final score = `base_relevance * base_weight + recency * recency_weight + importance * importance_weight - diversity_penalty`
