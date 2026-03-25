# AI Life OS — Architecture & Product-Driven Ideology

## Philosophy

AI Life OS is built on a single organising principle: **product requirements drive everything**.

Every feature begins as a codified requirement, flows through a domain plugin contract, gets auto-wired into every platform layer, and is verified by architecture tests that enforce traceability from requirement → scenario → test → implementation.

The goal: **a domain developer never thinks about infrastructure**. They define tools, agents, events, and memory categories in a single Python class. The kernel discovers, validates, and wires it all at startup. Architecture tests catch mistakes immediately. Product requirements ensure nothing is built that wasn't specified, and nothing specified goes untested.

```
Requirements (what to build)
    │
    ▼
Domain Plugin (how to build it)
    │
    ▼
Kernel Loader (auto-wire into every layer)
    │
    ▼
Architecture Tests (verify everything is connected)
    │
    ▼
Test Suite (prove it works — unit, integration, E2E, drift)
```

---

## The Three Pillars

### 1. Product Requirements as Code

Traditional product specs live in Notion or Google Docs and go stale within days. Our requirements live in the same repo as the code, in `tests/requirements/`.

```python
# tests/requirements/health.py
{
    "id": "REQ-HEALTH-001",
    "title": "Meal Logging via NLP",
    "description": "User can log a meal by describing it naturally...",
    "acceptance_criteria": [
        "User message 'I had eggs and toast' triggers health.log_meal tool",
        "Extracted items include 'eggs' and 'toast'",
        "Calorie estimate is returned in response",
        "Meal record is persisted with timestamp",
        "Event health.meal_logged is emitted",
    ],
    "priority": "P0",
}
```

**Benefits:**
- Requirements evolve with the code — same PR, same review
- Architecture tests auto-generate testable scenarios from acceptance criteria
- Coverage reports show exactly which requirements are tested and which aren't
- No separate traceability spreadsheet needed

**Domains covered:** `platform.py` (kernel), `health.py`, `finance.py`, `productivity.py`, `relationships.py`, `learning.py`, `home.py`

### 2. Domain Plugin Protocol

Every domain implements a single class that declares everything it needs from the platform:

```python
class HealthPlugin(DomainPlugin):
    domain_id = "health"

    def get_tools(self) -> list[ToolDeclaration]:       # What the LLM can call
    def get_agents(self) -> list[AgentDeclaration]:      # AI personalities
    def get_event_handlers(self) -> list[...]             # React to events
    def get_memory_categories(self) -> list[...]          # Structured fact types
    def get_router(self) -> APIRouter:                    # HTTP endpoints
```

The domain author provides these declarations. The platform does everything else.

### 3. Automated Enforcement

Architecture tests verify the entire system is correctly wired:

| Test | What it enforces |
|------|-----------------|
| `test_domain_integration.py` | Every domain plugin is wired into tools, agents, events, memory, routing |
| `test_domain_manifests.py` | Every domain has required files, valid manifest, naming conventions |
| `test_requirement_coverage.py` | Every P0 requirement has at least one tagged test |
| `test_scenario_generator.py` | Every acceptance criterion becomes a testable scenario |

These run on every push. A domain that's missing a tool handler, has a dangling agent-to-tool reference, or forgets to declare memory categories will fail CI immediately.

---

## System Layers

### Layer 0: Shared Infrastructure

```
src/shared/     Database sessions, base models, encryption, pagination, time utilities
src/config.py   Pydantic Settings (env vars)
src/main.py     FastAPI app factory + domain plugin loading
```

### Layer 1: Core Platform Modules

| Module | Responsibility |
|--------|---------------|
| `core/` | Tenants, users, workspaces, domain registry |
| `events/` | In-process event bus with pub/sub and wildcard matching |
| `communication/` | Channel adapters (WhatsApp, Telegram, REST) → inbound messages |
| `memory/` | Three-layer AI memory: short-term (Redis), structured (SQL), semantic (pgvector) |
| `knowledge/` | Document ingestion: parsing → chunking → embedding → storage |
| `retrieval/` | Hybrid RAG: semantic + structured + keyword search with reranking |
| `kernel/` | LLM client (LiteLLM), prompt registry, tool registry, global orchestrator |
| `orchestration/` | Multi-step workflow engine with branching and pause/resume |
| `agents/` | ReAct agent runtime: LLM → tool call → repeat → respond |
| `scheduling/` | APScheduler (cron) + arq (async background tasks) |
| `connectors/` | External service integration framework (OAuth, API keys, webhooks) |

### Layer 2: Domain Plugins

```
src/domains/
├── plugin.py       ← DomainPlugin base class + declaration data classes
├── loader.py       ← Auto-discovery and wiring at startup
├── health/         ← HealthPlugin: nutrition, exercise, sleep, vitals
├── finance/        ← FinancePlugin: transactions, budgets, investments
├── productivity/   ← ProductivityPlugin: tasks, habits, planning
├── relationships/  ← RelationshipsPlugin: contacts, interactions, dates
├── learning/       ← LearningPlugin: resources, sessions, notes
└── home/           ← HomePlugin: household tasks, shopping, maintenance
```

Each domain is a self-contained plugin. See `src/domains/README.md` for the developer guide.

---

## How a Domain Plugs Into Every Layer

When the application starts, `src/domains/loader.py` runs:

```
1. DISCOVER    Scan src/domains/*/__init__.py for `plugin` attribute
2. VALIDATE    Check naming conventions, tool references, structure
3. TOOLS       Register all ToolDeclarations into the ToolRegistry
4. AGENTS      Register all AgentDeclarations into the AgentRegistry
5. EVENTS      Subscribe all EventHandlerDeclarations to the EventBus
6. MEMORY      Register memory categories for structured facts
7. ROUTER      Mount the domain's FastAPI router at /api/v1/domains/{id}
8. LIFECYCLE   Call plugin.on_startup() for initialisation
9. REPORT      Log full wiring report (tools, agents, events, memory, router)
```

After startup, the registries are stored on `app.state` for dependency injection:

```python
app.state.tool_registry      # All domain tools, callable by agents
app.state.agent_registry     # All domain agents, routable by intent
app.state.event_bus           # All domain event handlers, subscribed
app.state.domain_wiring_report  # {domain_id: {tools: N, agents: N, ...}}
```

---

## How Requirements Flow Into Tests

```
┌─────────────────────────────────────────────────────────────────┐
│                     tests/requirements/health.py                 │
│  REQ-HEALTH-001: "Meal Logging via NLP"                          │
│  acceptance_criteria:                                            │
│    1. "User message 'eggs and toast' triggers health.log_meal"   │
│    2. "Extracted items include 'eggs' and 'toast'"               │
│    3. "Calorie estimate is returned"                             │
│    4. "Meal record is persisted"                                 │
│    5. "Event health.meal_logged is emitted"                      │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│           tests/arch/test_scenario_generator.py                  │
│  Auto-generates:                                                 │
│    SCN-REQ-HEALTH-001-01  (criterion 1)                          │
│    SCN-REQ-HEALTH-001-02  (criterion 2)                          │
│    SCN-REQ-HEALTH-001-03  (criterion 3)                          │
│    SCN-REQ-HEALTH-001-04  (criterion 4)                          │
│    SCN-REQ-HEALTH-001-05  (criterion 5)                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Actual test files                               │
│                                                                   │
│  @pytest.mark.req("REQ-HEALTH-001")                              │
│  @pytest.mark.scenario("SCN-REQ-HEALTH-001-01")                  │
│  def test_meal_message_triggers_log_meal_tool():                 │
│      ...                                                         │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│           tests/arch/test_requirement_coverage.py                │
│  Scans test files for @pytest.mark.req() markers                 │
│  Reports: "REQ-HEALTH-001: ✓ 3 test(s)"                         │
│  Fails if P0 requirements have 0 tests                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Test Tiers

| Tier | Purpose | Speed | Dependencies |
|------|---------|-------|-------------|
| **Unit** | Isolated logic correctness | ~1s | Mocks only |
| **Integration** | Cross-module data flows | ~5s | Real SQLite, mock Redis |
| **E2E** | Full user scenarios | ~10s | Cassettes (recorded LLM) |
| **Drift** | Prompt/model regression | ~30s | Real gpt-4o-mini, temp=0 |
| **Arch** | Structure + coverage enforcement | ~2s | File system scan |

### Typical development workflow

```
Write daily:        Unit + Integration tests        (instant feedback)
Run on PR:          + E2E with cassettes             (deterministic)
Run nightly:        + Drift with real LLM            (catch model changes)
Run always:         + Arch tests                     (catch structural drift)
```

### Cassette workflow for E2E

1. **Develop** with cassettes (recorded LLM responses) for speed and determinism
2. **Record** new cassettes when prompts change: `RECORD_CASSETTES=1 pytest tests/e2e/`
3. **Replay** in CI (default mode) — no API key needed, instant, reproducible
4. **Drift test nightly** with real LLM calls to catch model behavioural changes

---

## CI Pipeline

| Trigger | Tests | Duration |
|---------|-------|----------|
| Every push | `pytest tests/unit/ tests/arch/` | ~3s |
| Pull request | `pytest tests/ --ignore=tests/drift` | ~15s |
| Merge to main | Full suite + coverage report | ~20s |
| Nightly cron | `RUN_DRIFT_TESTS=1 pytest tests/drift/ -m drift` | ~30s |

---

## Adding a New Domain

A domain developer follows these steps:

1. **Define requirements** in `tests/requirements/{domain}.py`
2. **Create plugin class** in `src/domains/{domain}/__init__.py` (subclass `DomainPlugin`)
3. **Implement stubs** for tools, agents, event handlers
4. **Create router** in `src/domains/{domain}/router.py`
5. **Write tests** tagged with `@pytest.mark.req("REQ-{DOMAIN}-001")`
6. **Run arch tests** — they verify everything is wired correctly

The developer never:
- Manually registers tools in the kernel
- Manually subscribes event handlers
- Manually mounts routers in main.py
- Manually updates any global registry

The kernel handles all of it. The arch tests verify all of it.

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Requirements as Python dicts, not Markdown | Machine-readable → auto-generate scenarios, auto-check coverage |
| DomainPlugin ABC, not registration decorators | Explicit contract → IDE autocomplete, validate() method, clear errors |
| Auto-wiring at startup, not import-time | Testable in isolation, clean startup logs, wiring report |
| Arch tests, not runtime checks | Fail at CI time, not at 3am in production |
| Cassettes for E2E, real LLM for drift | Deterministic CI + nightly regression = best of both worlds |
| Stub handlers, not empty plugins | Every tool is invocable from day one, even before Phase 1 implementation |
