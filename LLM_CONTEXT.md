# AI Life OS — Full Development Context for LLM Handoff

> **Purpose:** Feed this entire document as a single message to any LLM to give it complete context about the AI Life OS project — architecture, codebase structure, what's been built, what's pending, and all design decisions. This replaces conversation history.

---

## Project Identity

- **Name:** AI Life OS
- **Repo:** `/Users/ykodesia/Desktop/github/lifeOS/`
- **GitHub:** https://github.com/KodesiaYash/lifeOS
- **Phase:** Phase 0 complete (kernel foundation). Phase 1 (domain implementations) pending.
- **Tech stack:** Python 3.11+, FastAPI, SQLAlchemy 2.0 async, PostgreSQL 16 + pgvector, Redis 7, LiteLLM, structlog, Pydantic Settings, APScheduler, arq, Docker Compose.
- **Mode:** Single-user (self-hosted). Multi-tenancy can be added later for SaaS.

---

## What This Project Is

An AI-powered **personal** life management platform designed to run on your own hardware (Mac Mini, PC, etc.). Users interact via WhatsApp/Telegram/REST. The AI understands intent, routes to domain-specific agents (health, finance, productivity, relationships, learning, home), calls tools, remembers context across conversations, and provides personalised responses.

Built as a **modular monolith** — one deployable with clean module boundaries, event-driven communication, and a plugin architecture for domains.

**Single-user by design:** Clone the repo, run it, and it works for you. No tenant or user IDs required. The architecture is extensible for multi-tenancy later if you want to offer it as a SaaS.

---

## Architecture: Product-Driven Ideology

The core organising principle: **product requirements drive everything**.

```
Requirements (tests/requirements/*.py)
    → Domain Plugin (src/domains/{domain}/__init__.py)
        → Kernel Auto-Wiring (src/domains/loader.py)
            → Architecture Tests verify it all (tests/arch/)
                → Test Suite proves it works (tests/unit|integration|e2e|drift/)
```

A domain developer only implements one Python class (`DomainPlugin` subclass). The kernel discovers, validates, and wires it into every platform layer at startup. Architecture tests catch any mistakes at CI time, not runtime.

Full documentation: `ARCHITECTURE.md` (project root).

---

## Codebase Structure

```
src/
├── config.py                # Pydantic Settings (env vars)
├── main.py                  # FastAPI app factory + domain plugin loading in lifespan
├── dependencies.py          # DI: db session only (no tenant/user context needed)
├── shared/                  # Database, base models, crypto, pagination, time
│   └── base_model.py        # Base, TimestampedBase (no tenant_id)
├── core/                    # Settings, domain registry (no tenants/users)
│   ├── models.py            # Settings, DomainRegistry
│   ├── schemas.py           # SettingsRead/Update, DomainRegistryRead/Update
│   └── middleware.py        # RequestContextMiddleware (request tracing)
├── events/                  # Event bus (pub/sub) with wildcard matching
│   └── bus.py               # EventBus class — _handlers dict, publish(), subscribe()
├── communication/           # Channel adapters (WhatsApp, Telegram, REST)
├── memory/                  # Short-term (Redis), structured (SQL), semantic (pgvector)
│   └── schemas.py           # MemoryPacket, MemoryFactCreate, SemanticMemoryCreate
├── knowledge/               # Document ingestion, chunking, embedding
│   └── chunking.py          # TextChunker, estimate_tokens
├── retrieval/               # Hybrid RAG: semantic + structured + keyword + reranker
│   └── reranker.py          # Reranker with recency_boost, diversity_penalty, importance_weight
├── kernel/                  # LLM client (LiteLLM), prompt registry, tool registry
│   ├── tool_registry.py     # ToolRegistry: register(), get(), invoke(), list_tools(domain=)
│   ├── prompt_registry.py   # PromptRegistry: register(), render(), list_prompts()
│   └── llm_client.py        # LLMClient wrapping LiteLLM
├── orchestration/           # Workflow engine with step types
├── agents/                  # Agent runtime with ReAct tool-calling loop
│   ├── registry.py          # AgentRegistry: register(), get(), list_agents(domain=)
│   └── schemas.py           # AgentDefinitionRead, AgentInvokeRequest/Response
├── scheduling/              # APScheduler (cron) + arq (async tasks)
├── connectors/              # External service integration framework
│   └── base.py              # BaseConnector ABC: authenticate, sync, handle_webhook
└── domains/                 # Domain plugin system
    ├── plugin.py            # DomainPlugin ABC + ToolDeclaration, AgentDeclaration, etc.
    ├── loader.py            # discover_domain_plugins(), load_domain_plugins()
    ├── README.md            # Domain developer guide
    ├── health/              # HealthPlugin: 5 tools, 2 agents, 2 event handlers, 5 memory cats
    ├── finance/             # FinancePlugin: 4 tools, 1 agent, 2 event handlers, 5 memory cats
    ├── productivity/        # ProductivityPlugin: 5 tools, 2 agents, 2 event handlers, 5 memory cats
    ├── relationships/       # RelationshipsPlugin: 4 tools, 1 agent, 2 event handlers, 4 memory cats
    ├── learning/            # LearningPlugin: 4 tools, 2 agents, 2 event handlers, 5 memory cats
    └── home/                # HomePlugin: 4 tools, 1 agent, 2 event handlers, 5 memory cats
```

### Key files you'll edit most often:
- `src/domains/{domain}/__init__.py` — Domain plugin class + tool handlers
- `src/domains/{domain}/models.py` — SQLAlchemy models (empty stubs, Phase 1)
- `src/domains/{domain}/router.py` — FastAPI endpoints
- `tests/requirements/{domain}.py` — Product requirements
- `tests/unit/test_{module}/` — Unit tests

---

## Domain Plugin System (The Core Innovation)

Every domain implements `DomainPlugin` from `src/domains/plugin.py`:

```python
class HealthPlugin(DomainPlugin):
    domain_id = "health"
    name = "Health & Fitness"
    version = "0.1.0"

    def get_tools(self) -> list[ToolDeclaration]:        # Functions the LLM calls
    def get_agents(self) -> list[AgentDeclaration]:       # AI personalities
    def get_event_handlers(self) -> list[EventHandlerDeclaration]:  # React to events
    def get_memory_categories(self) -> list[MemoryCategoryDeclaration]:  # Fact types
    def get_router(self) -> APIRouter:                    # HTTP endpoints
```

Last line of `__init__.py` must be: `plugin = HealthPlugin()`

At startup, `src/domains/loader.py` auto-wires every plugin into:
1. **ToolRegistry** — tools callable by agents/LLM
2. **AgentRegistry** — agents routable by intent classification
3. **EventBus** — event handlers subscribed to patterns
4. **Memory categories** — registered for the memory assembler
5. **FastAPI router** — mounted at `/api/v1/domains/{domain_id}`

Registries stored on `app.state` for dependency injection.

### Current domain totals:
- **26 tools**, **9 agents**, **12 event handlers**, **29 memory categories** across 6 domains
- All handlers are async stubs returning `{"status": "stub", ...}` — ready for Phase 1 implementation

### Naming convention (enforced by validate()):
- Tools: `{domain}.{action}` → `health.log_meal`
- Agents: `{domain}.{role}` → `health.nutrition_coach`
- Events: `{domain}.{event}` → `health.meal_logged`

---

## Test Suite Architecture

```
tests/
├── conftest.py              # Root fixtures: async event loop, in-memory SQLite, identity UUIDs
├── unit/                    # 15 test files — isolated logic, mocks only
│   ├── conftest.py          # Mock event bus, LLM client, DB session, prompt/tool registries
│   ├── test_shared/         # test_crypto.py, test_time.py, test_pagination.py
│   ├── test_core/           # test_schemas.py (TenantCreate, UserCreate, WorkspaceCreate)
│   ├── test_events/         # test_bus.py (subscribe, wildcard, publish, error handling)
│   ├── test_communication/  # test_schemas.py (InboundMessageCreate, MessageType)
│   ├── test_memory/         # test_schemas.py (MemoryFactCreate, SemanticMemoryCreate, MemoryPacket)
│   ├── test_knowledge/      # test_chunking.py (TextChunker, estimate_tokens)
│   ├── test_retrieval/      # test_reranker.py, test_schemas.py
│   ├── test_kernel/         # test_prompt_registry.py, test_tool_registry.py
│   ├── test_agents/         # test_registry.py, test_schemas.py
│   ├── test_orchestration/  # test_schemas.py (WorkflowStatus, StepType, TriggerType)
│   ├── test_scheduling/     # test_schemas.py (ScheduleType, TaskStatus, ScheduledJobCreate)
│   └── test_connectors/     # test_schemas.py (ConnectorDefinition, SyncLogRead)
├── integration/             # Cross-module flows
│   ├── test_event_flow.py   # Multiple handlers, wildcard routing, correlation_id propagation
│   ├── test_knowledge_flow.py # Chunking → token estimation → content completeness
│   └── test_tool_agent_flow.py # Tool+agent registry wiring, invocation, graceful failures
├── e2e/                     # Full pipeline with cassettes
│   ├── conftest.py          # CassetteManager (record/replay LLM calls)
│   └── test_message_to_response.py # Meal log pipeline, greeting, context injection
├── drift/                   # Nightly real-LLM tests
│   ├── conftest.py          # RUN_DRIFT_TESTS=1 gate, OPENAI_API_KEY required
│   └── test_intent_classification.py # 6 tests: meal, budget, task, greeting, ambiguous, multi-domain
├── arch/                    # Architecture enforcement
│   ├── test_requirement_coverage.py  # Scans @pytest.mark.req() tags, reports coverage
│   ├── test_domain_manifests.py      # Domain files, manifest keys, naming conventions
│   ├── test_domain_integration.py    # ALL-LAYER verification per domain (the big one)
│   └── test_scenario_generator.py    # Generates SCN-* from acceptance criteria
└── requirements/            # Product requirements as code
    ├── platform.py          # REQ-PLAT-001 through 009 (kernel requirements)
    ├── health.py            # REQ-HEALTH-001 through 008
    ├── finance.py           # REQ-FIN-001 through 005
    ├── productivity.py      # REQ-PROD-001 through 006
    ├── relationships.py     # REQ-REL-001 through 004
    ├── learning.py          # REQ-LEARN-001 through 005
    └── home.py              # REQ-HOME-001 through 004
```

### Test tagging for traceability:
```python
@pytest.mark.req("REQ-HEALTH-001")
@pytest.mark.scenario("SCN-REQ-HEALTH-001-01")
def test_meal_message_triggers_log_meal_tool():
    ...
```

### Custom pytest markers (in pyproject.toml):
- `req(id)` — links test to a product requirement
- `scenario(id)` — links test to a generated scenario
- `drift` — nightly real-LLM test

### CI pipeline:
| Trigger | Command | Duration |
|---------|---------|----------|
| Every push | `pytest tests/unit/ tests/arch/` | ~3s |
| Pull request | `pytest tests/ --ignore=tests/drift` | ~15s |
| Merge to main | Full suite + coverage | ~20s |
| Nightly cron | `RUN_DRIFT_TESTS=1 pytest tests/drift/ -m drift` | ~30s |

---

## Product Requirements Summary

41 requirements across 7 files:

**Platform (REQ-PLAT-001–009):** Multi-tenant isolation, event bus, 3-layer memory, hybrid RAG, agent ReAct loop, workflow engine, connector framework, credential encryption, domain plugin architecture.

**Health (REQ-HEALTH-001–008):** Meal logging NLP, exercise logging, sleep logging, nutrition summary, dietary preference memory, health goals, nutrition coach agent, vitals recording.

**Finance (REQ-FIN-001–005):** Transaction logging NLP, spending summary, budget management, financial goals, budget advisor agent.

**Productivity (REQ-PROD-001–006):** Task creation NLP, task completion, task listing, habit tracking, daily summary, planner agent.

**Relationships (REQ-REL-001–004):** Interaction logging, contact management, interaction history, important date reminders.

**Learning (REQ-LEARN-001–005):** Resource tracking, study sessions, progress query, note capture, AI tutor agent.

**Home (REQ-HOME-001–004):** Household tasks, shopping lists, maintenance scheduling, household manager agent.

---

## Key Technical Details

### Single-User Architecture
- **No tenant_id or user_id** — All data belongs to the single user running the app
- **`TimestampedBase`** — Base class for models with id, created_at, updated_at, deleted_at
- **`Settings`** model — Singleton for app preferences (timezone, language, active_domains)
- **Extensible for multi-tenancy** — Add tenant_id column and filtering later if needed

### EventBus (`src/events/bus.py`)
- Internal attribute: `_handlers` (defaultdict of lists), NOT `_subscribers`
- Wildcard: `health.*` matches `health.meal_logged`, `health.exercise_logged`
- Handler errors are caught and logged, don't block other handlers
- Singleton: `event_bus = EventBus()`

### ToolRegistry (`src/kernel/tool_registry.py`)
- `register(definition, implementation)` — stores ToolDefinition + callable
- `invoke(tool_id, **kwargs)` → ToolResult(success, data, error)
- Supports both sync and async handlers (auto-detected via `inspect.iscoroutinefunction`)
- `get_openai_tools(domain=)` — exports in OpenAI function-calling format

### AgentRegistry (`src/agents/registry.py`)
- `register(AgentDefinitionRead)`, `get(agent_type)`, `list_agents(domain=)`
- `unregister(agent_type)`, `list_agent_types()`

### Memory System
- **Short-term:** Redis with TTL (session context)
- **Structured:** SQL facts with category, key, value, confidence (no user scoping needed)
- **Semantic:** pgvector embeddings for fuzzy recall
- **MemoryPacket:** Combined output from all three layers for prompt injection

### Crypto (`src/shared/crypto.py`)
- Fernet encryption for credentials at rest
- `encrypt(plaintext) → ciphertext`, `decrypt(ciphertext) → plaintext`
- Same plaintext produces different ciphertext (random IV)

---

## What's Complete (Phase 0)

All 18 steps of Phase 0 are done:
1. Project skeleton (pyproject.toml, Dockerfile, docker-compose.yml, .env.example, alembic)
2. Shared utilities (database, base_model, crypto, pagination, time)
3. Config & app entry (config.py, main.py with domain plugin loading, dependencies.py)
4. Core module (tenants, users, workspaces, domain registry)
5. Events module (event bus pub/sub, event log)
6. Communication module (WhatsApp/Telegram/REST adapters, conversations, messages)
7. Memory module (short-term Redis, structured SQL, semantic pgvector, assembler, consolidation)
8. Knowledge module (documents, chunks, ingestion pipeline, chunking, embedding, parsers, tagging)
9. Retrieval module (semantic/structured/keyword retrievers, reranker, coordinator)
10. Kernel module (LLM client via LiteLLM, prompt/tool registries, global orchestrator)
11. Orchestration module (workflow engine with step types)
12. Agents module (runtime with ReAct tool-calling, registry)
13. Scheduling module (APScheduler + arq worker)
14. Domain plugin system (DomainPlugin protocol, loader, all 6 domains implemented)
15. Connectors scaffold (base connector, service, models)
16. Seed data script (scripts/seed.py)
17. Full test suite (unit/integration/e2e/drift/arch + requirements + README)
18. Documentation (ARCHITECTURE.md, per-module READMEs, domain developer guide, tests README)

---

## What's Pending (Phase 1)

Phase 1 = **implement real domain logic** (replace stub handlers with actual functionality):

1. **Health domain:** Real meal parsing (NLP → food items → calorie estimation), exercise/sleep logging, nutrition summaries, vitals recording. SQLAlchemy models: MealLog, ExerciseLog, SleepLog, VitalsRecord, HealthGoal.

2. **Finance domain:** Transaction parsing, spending summaries, budget tracking. Models: Transaction, Budget, FinancialGoal.

3. **Productivity domain:** Task CRUD, habit tracking with streaks, daily summaries. Models: Task, Habit, Project.

4. **Relationships domain:** Contact management, interaction logging, reminder scheduling. Models: Contact, Interaction, ImportantDate.

5. **Learning domain:** Resource tracking, session logging, note capture, RAG over learning materials. Models: LearningResource, StudySession, LearningNote.

6. **Home domain:** Household task management, shopping lists, maintenance scheduling. Models: HouseholdTask, ShoppingList, MaintenanceSchedule.

7. **Intent classification:** Real LLM-based routing (message → domain → agent).

8. **Tag all tests with `@pytest.mark.req()`** for full requirement traceability.

9. **Record E2E cassettes** for real LLM interactions.

---

## Configuration

### Key files:
- `pyproject.toml` — dependencies, pytest config, ruff config, mypy config
- `.env.example` → `.env` — DATABASE_URL, REDIS_URL, OPENAI_API_KEY, FERNET_KEY, etc.
- `docker-compose.yml` — postgres, redis, minio, app, worker
- `alembic/` — database migrations

### pytest config (in pyproject.toml):
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
markers = [
    "req(id): Link test to a product requirement",
    "scenario(id): Link test to a generated scenario",
    "drift: Nightly real-LLM drift test",
]
```

### Dev dependencies:
pytest, pytest-asyncio, pytest-cov, httpx, factory-boy, ruff, mypy, pre-commit, aiosqlite, respx

---

## Important Conventions

1. **Single-user mode** — No tenant_id or user_id in models, schemas, or dependencies
2. **All tool handlers must be async** — enforced by arch tests
3. **All identifiers namespaced with domain** — `health.log_meal`, not `log_meal`
4. **Every domain exports `plugin = MyPlugin()`** in `__init__.py`
5. **Requirements are Python dicts** in `tests/requirements/`, not Markdown
6. **Each test file has a module docstring** listing every test function and what it does
7. **Stubs return** `{"status": "stub", "action": "...", "input": kwargs}`
8. **Static manifest.py and plugin declarations must stay in sync** — arch tests verify
9. **Event bus uses `_handlers`** internally (not `_subscribers`)
10. **No flat test files** — everything is in `tests/{tier}/test_{module}/`
11. **Cassettes for E2E, real LLM for drift** — never real LLM in CI except nightly
12. **`TimestampedBase`** for all domain models (provides id, created_at, updated_at, deleted_at)
