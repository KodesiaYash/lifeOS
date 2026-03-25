# AI Life OS — Kernel Foundation (Phase 0)

An AI-powered life management platform built as a modular monolith. The kernel provides multi-tenant infrastructure, a three-layer memory system, hybrid RAG retrieval, workflow orchestration, agent runtime, and pluggable domain scaffolds.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                    │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│   Core   │  Events  │  Comms   │  Memory  │  Knowledge  │
├──────────┼──────────┼──────────┴──────────┼─────────────┤
│ Retrieval│  Kernel  │  Orchestration      │   Agents    │
├──────────┼──────────┼─────────────────────┼─────────────┤
│Scheduling│Connectors│     6 Domain Plugins (scaffolds)  │
├──────────┴──────────┴───────────────────────────────────┤
│         PostgreSQL (pgvector)  │  Redis  │  MinIO       │
└─────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.11+ |
| **Web Framework** | FastAPI |
| **ORM** | SQLAlchemy 2.0 (async) |
| **Migrations** | Alembic |
| **Database** | PostgreSQL 16 + pgvector |
| **Cache / Queue** | Redis 7 |
| **Object Storage** | MinIO (S3-compatible) |
| **LLM Client** | LiteLLM + OpenAI |
| **Structured Output** | Instructor |
| **Scheduling** | APScheduler (cron) + arq (async tasks) |
| **Logging** | structlog (JSON) |
| **Config** | Pydantic Settings |
| **Containerization** | Docker + Docker Compose |

## Project Structure

```
src/
├── config.py              # Pydantic Settings
├── main.py                # FastAPI app factory
├── dependencies.py        # DI: db session, tenant_id, user_id
├── shared/                # Database, base models, crypto, pagination, time
├── core/                  # Tenants, users, workspaces, domain registry
├── events/                # Event bus (pub/sub) + event log
├── communication/         # Channel adapters (WhatsApp, Telegram, REST)
├── memory/                # Short-term (Redis), structured (SQL), semantic (pgvector)
├── knowledge/             # Document ingestion, chunking, embedding, parsers
├── retrieval/             # Hybrid RAG: semantic + structured + keyword + reranker
├── kernel/                # LLM client, prompt/tool registries, orchestrator
├── orchestration/         # Workflow engine with step types
├── agents/                # Agent runtime with ReAct tool-calling loop
├── scheduling/            # APScheduler + arq worker
├── connectors/            # External service integration framework
└── domains/               # Domain plugin scaffolds
    ├── health/
    ├── finance/
    ├── productivity/
    ├── relationships/
    ├── learning/
    └── home/
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+

### 1. Clone & configure

```bash
cp .env.example .env
# Edit .env with your API keys and secrets
```

### 2. Start infrastructure

```bash
docker compose up -d postgres redis minio
```

### 3. Install dependencies

```bash
pip install -e ".[dev]"
```

### 4. Run migrations

```bash
alembic upgrade head
```

### 5. Seed data

```bash
python -m scripts.seed
```

### 6. Start the app

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Start background worker

```bash
arq src.scheduling.worker.WorkerSettings
```

## Docker Compose (full stack)

```bash
docker compose up --build
```

Services: `app` (8000), `worker`, `postgres` (5432), `redis` (6379), `minio` (9000/9001).

## Running Tests

```bash
# Unit tests (fastest — < 2s)
pytest tests/unit/ -v

# All tests except drift (CI default)
pytest tests/ -v --ignore=tests/drift

# Architecture tests (verify domain wiring + requirement coverage)
pytest tests/arch/ -v -s

# Drift tests (nightly, requires real LLM)
RUN_DRIFT_TESTS=1 OPENAI_API_KEY=sk-... pytest tests/drift/ -m drift -v

# Coverage report
pytest tests/ --cov=src --cov-report=html --ignore=tests/drift
```

See [`tests/README.md`](tests/README.md) for the full test architecture and product-driven testing philosophy.

## Module Documentation

Each module has its own README:

- [`src/shared/README.md`](src/shared/README.md) — Database, base models, crypto, time utilities
- [`src/core/README.md`](src/core/README.md) — Multi-tenant core entities
- [`src/events/README.md`](src/events/README.md) — Event bus and event log
- [`src/communication/README.md`](src/communication/README.md) — Channel adapters and messaging
- [`src/memory/README.md`](src/memory/README.md) — Three-layer memory system
- [`src/knowledge/README.md`](src/knowledge/README.md) — Knowledge ingestion pipeline
- [`src/retrieval/README.md`](src/retrieval/README.md) — Hybrid RAG retrieval
- [`src/kernel/README.md`](src/kernel/README.md) — AI kernel and orchestrator
- [`src/orchestration/README.md`](src/orchestration/README.md) — Workflow engine
- [`src/agents/README.md`](src/agents/README.md) — Agent runtime
- [`src/scheduling/README.md`](src/scheduling/README.md) — Scheduling system
- [`src/connectors/README.md`](src/connectors/README.md) — External connectors

## Design Documents

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — Product-driven ideology, domain plugin system, testing philosophy
- [`docs/SYSTEM_DESIGN.md`](docs/SYSTEM_DESIGN.md) — Full system architecture
- [`docs/SCHEMA_DESIGN.md`](docs/SCHEMA_DESIGN.md) — Database schema reference
- [`src/domains/README.md`](src/domains/README.md) — Domain plugin developer guide
- [`tests/README.md`](tests/README.md) — Test suite architecture + requirement traceability

## Phase 0 Deliverables

- [x] Project skeleton & Docker infrastructure
- [x] Shared utilities (database, crypto, pagination, time)
- [x] Config & FastAPI app entry point
- [x] Core module (tenants, users, workspaces, domain registry)
- [x] Events module (event bus, event log)
- [x] Communication module (channel adapters, conversations, messages)
- [x] Memory module (short-term, structured, semantic, assembler)
- [x] Knowledge module (documents, chunks, ingestion pipeline, parsers)
- [x] Retrieval module (semantic, structured, keyword, reranker, coordinator)
- [x] Kernel module (LLM client, prompt/tool registries, orchestrator)
- [x] Orchestration module (workflow engine with step types)
- [x] Agents module (runtime, registry)
- [x] Scheduling module (APScheduler + arq)
- [x] Domain plugin scaffolding (6 domains)
- [x] Connectors scaffold
- [x] Seed scripts
- [x] Tests
- [x] Documentation (per-module READMEs + global README)

## License

Private — All rights reserved.
