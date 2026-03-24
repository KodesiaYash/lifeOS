# Memory Module (`src/memory/`)

Three-layer memory fabric: short-term (Redis), structured (SQL), and semantic (pgvector).

## Contents

| File | Purpose |
|------|---------|
| `models.py` | SQLAlchemy models: MemoryFact, SemanticMemory, ConversationSummary |
| `schemas.py` | Pydantic schemas: MemoryFactCreate/Read, SemanticMemoryCreate/Read, MemoryPacket |
| `repository.py` | Database access for all memory tables (including pgvector similarity search) |
| `short_term.py` | `ShortTermMemory` — Redis-backed session state with TTL |
| `structured.py` | `StructuredMemory` — SQL-backed fact store with supersession |
| `semantic.py` | `SemanticMemoryStore` — pgvector-backed semantic search |
| `assembler.py` | `MemoryAssembler` — gathers context from all layers into a bounded `MemoryPacket` |
| `consolidation.py` | `MemoryConsolidator` — background jobs for session summarization, pattern extraction, dedup |

## Memory Layers

1. **Short-term** (Redis): Active session state, recent message history. TTL = 2 hours.
2. **Structured** (PostgreSQL): Discrete key-value facts with categories. Supports supersession.
3. **Semantic** (pgvector): Natural language memories with embeddings for similarity search.

## Assembly

`MemoryAssembler.assemble()` gathers from all layers within a token budget:
- Priority: session context → facts → semantic matches → conversation summaries
- Default budget: 3000 tokens
