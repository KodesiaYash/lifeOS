# AI Life OS — Kernel Foundation (Phase 0)

An AI-powered life management platform built as a modular monolith. The kernel provides a three-layer memory system, hybrid RAG retrieval, workflow orchestration, agent runtime, and pluggable domain scaffolds. Designed for single-user self-hosting.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                    │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│   Core   │  Events  │  Comms   │  Memory  │  Knowledge  │
├──────────┼──────────┼──────────┴──────────┼─────────────┤
│ Retrieval│  Kernel  │  Orchestration      │   Agents    │
├──────────┼──────────┼─────────────────────┼─────────────┤
│Scheduling│Connectors│     7 Domain Plugins (scaffolds)  │
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
├── dependencies.py        # DI: db session
├── shared/                # Database, base models, crypto, pagination, time
├── core/                  # Settings, domain registry
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
    ├── home/
    └── dutch_tutor/
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

### 2. Start the full local stack

```bash
docker compose up --build
```

The stack brings up:

- `app` on `http://localhost:8000`
- `worker`
- `postgres` on `localhost:5432`
- `redis` on `localhost:6379`
- `minio` on `localhost:9000` and `localhost:9001`

### 3. Install dependencies for local Python workflows

```bash
pip install -e ".[dev]"
```

### 4. Validate the promoted Dutch tutor domain

```bash
curl -X POST http://localhost:8000/api/v1/domains/dutch_tutor/translate \
  -H "Content-Type: application/json" \
  -d '{"word":"huis"}'
```

Expected response includes:

- `english_word: "house"`
- `back_to_dutch: "huis"`

### 5. Optional manual workflows

```bash
alembic upgrade head
python -m scripts.seed
arq src.scheduling.worker.WorkerSettings
```

## Telegram Setup

```bash
export TELEGRAM_WEBHOOK_URL="https://<your-public-url>/api/v1/communication/webhooks/telegram"
```

When `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, and `TELEGRAM_WEBHOOK_URL` are set, the app registers the webhook on startup. For local Telegram testing, expose port `8000` through a tunnel such as Cloudflare Tunnel or ngrok and point `TELEGRAM_WEBHOOK_URL` at that public HTTPS URL.

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
- [`src/core/README.md`](src/core/README.md) — Settings and domain registry
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
- [`docs/ARCHITECTURE_CONTRACT.md`](docs/ARCHITECTURE_CONTRACT.md) — Change contract for inbound flow, orchestration, events, memory, and tests
- [`docs/SYSTEM_DESIGN.md`](docs/SYSTEM_DESIGN.md) — Full system architecture
- [`docs/SCHEMA_DESIGN.md`](docs/SCHEMA_DESIGN.md) — Database schema reference
- [`src/domains/README.md`](src/domains/README.md) — Domain plugin developer guide
- [`tests/README.md`](tests/README.md) — Test suite architecture + requirement traceability

## Phase 0 Deliverables

- [x] Project skeleton & Docker infrastructure
- [x] Shared utilities (database, crypto, pagination, time)
- [x] Config & FastAPI app entry point
- [x] Core module (settings, domain registry)
- [x] Events module (event bus, event log)
- [x] Communication module (channel adapters, conversations, messages)
- [x] Memory module (short-term, structured, semantic, assembler)
- [x] Knowledge module (documents, chunks, ingestion pipeline, parsers)
- [x] Retrieval module (semantic, structured, keyword, reranker, coordinator)
- [x] Kernel module (LLM client, prompt/tool registries, orchestrator)
- [x] Orchestration module (workflow engine with step types)
- [x] Agents module (runtime, registry)
- [x] Scheduling module (APScheduler + arq)
- [x] Domain plugin scaffolding (7 domains, including `dutch_tutor`)
- [x] Connectors scaffold
- [x] Seed scripts
- [x] Tests
- [x] Documentation (per-module READMEs + global README)

## License

Private — All rights reserved.
