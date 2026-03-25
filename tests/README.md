# AI Life OS — Test Suite

Modular, multi-tier test suite with product requirement traceability and LLM drift detection.

## Product-Driven Testing Philosophy

This test suite is built on a core belief: **tests exist to prove product requirements are met, not just that code doesn't crash**.

Every test should trace back to a product requirement. Every product requirement should generate testable scenarios. Architecture tests enforce this traceability automatically — no manual spreadsheets, no stale Confluence pages.

```
Product Requirement  →  Acceptance Criteria  →  Generated Scenarios  →  Tagged Tests
     (human)               (human)              (automated)            (developer)
```

The flow works in both directions:
- **Top-down:** "REQ-HEALTH-001 needs tests" → developer writes tests tagged with `@pytest.mark.req("REQ-HEALTH-001")`
- **Bottom-up:** "This test covers which requirement?" → the `@pytest.mark.req()` tag answers that instantly

The arch tests close the loop: `test_requirement_coverage.py` scans every test file for `@pytest.mark.req()` markers and reports which requirements are covered, which are not, and which have excess tests with no matching requirement (a sign of accidental scope creep).

### Why requirements live in `tests/requirements/` and not a wiki

| Traditional approach | Our approach |
|---------------------|-------------|
| Requirements in Notion | Requirements in `tests/requirements/*.py` |
| Tests in `tests/` | Tests in `tests/` with `@pytest.mark.req()` tags |
| Manual traceability matrix | **Automated** — arch tests scan for markers |
| Stale within a week | Always in sync — lives in the same repo |
| "Did we test that?" → search Jira | `pytest tests/arch/ -v -s` → instant coverage report |

### Domain integration testing

Every domain plugin is verified against ALL platform layers by `test_domain_integration.py`:

| Layer | What's checked |
|-------|---------------|
| **Discovery** | Plugin class exists, inherits DomainPlugin, passes validate() |
| **Tools** | Every tool has async handler, correct `{domain}.` prefix, meaningful description |
| **Agents** | Every agent has system prompt, tools list references only declared tools |
| **Events** | Every handler is async, pattern is namespaced with `{domain}.` |
| **Memory** | Every category has description and example keys |
| **Router** | Plugin provides a FastAPI APIRouter |
| **Cross-layer** | No dangling tool references, no ID collisions across domains |
| **Manifest** | Plugin's generated manifest matches static `manifest.py` |
| **Full wiring** | Simulated startup: all tools, agents, events register without errors |

This means a domain developer gets immediate feedback if they:
- Forget to declare a tool their agent references
- Name a tool `log_meal` instead of `health.log_meal`
- Provide a sync handler instead of async
- Leave a memory category without example keys
- Don't export `plugin = MyPlugin()` in `__init__.py`

## Test Architecture

```
tests/
├── conftest.py                     ← Root fixtures: DB, identity, timestamps
├── README.md                       ← This file
│
├── unit/                           ← Isolated logic tests, mocks only, no I/O
│   ├── conftest.py                 ← Mock LLM, mock DB, mock Redis
│   ├── test_shared/                ← Crypto, time, pagination
│   ├── test_core/                  ← Core entity schemas
│   ├── test_events/                ← Event bus subscribe/publish/wildcard
│   ├── test_communication/         ← Inbound message, message type schemas
│   ├── test_memory/                ← Memory fact, semantic memory, memory packet schemas
│   ├── test_knowledge/             ← Text chunking, token estimation
│   ├── test_retrieval/             ← Reranker scoring, retrieval schemas
│   ├── test_kernel/                ← Prompt registry, tool registry
│   ├── test_agents/                ← Agent registry, invocation schemas
│   ├── test_orchestration/         ← Workflow status, step types, trigger types
│   ├── test_scheduling/            ← Schedule types, task status, job/task schemas
│   └── test_connectors/            ← Connector definition, instance, sync log schemas
│
├── integration/                    ← Cross-module flows with real DB
│   ├── conftest.py                 ← Real SQLite, mock Redis, mock embeddings
│   ├── test_event_flow.py          ← Event bus → multiple handlers → payload propagation
│   ├── test_knowledge_flow.py      ← Chunking → token estimation → ingestion pipeline
│   └── test_tool_agent_flow.py     ← Tool registry → agent registry → invocation wiring
│
├── e2e/                            ← Full pipeline tests with cassettes
│   ├── conftest.py                 ← Cassette manager, mock LLM responses
│   └── test_message_to_response.py ← Inbound message → intent → agent → tool → response
│
├── drift/                          ← Nightly real-LLM behavioural tests
│   ├── conftest.py                 ← Skip logic, drift_test decorator
│   └── test_intent_classification.py ← Real LLM intent classification accuracy
│
├── arch/                           ← Architecture & requirement coverage enforcement
│   ├── test_requirement_coverage.py ← Verifies every P0 requirement has tagged tests
│   ├── test_domain_manifests.py    ← Verifies domain plugin structure + naming
│   ├── test_domain_integration.py  ← Verifies every domain wired into ALL layers
│   └── test_scenario_generator.py  ← Generates scenarios from requirements, checks coverage
│
├── requirements/                   ← Product requirements as code
│   ├── platform.py                 ← Kernel/cross-cutting requirements (REQ-PLAT-*)
│   ├── health.py                   ← Health domain requirements (REQ-HEALTH-*)
│   ├── finance.py                  ← Finance domain requirements (REQ-FIN-*)
│   ├── productivity.py             ← Productivity domain requirements (REQ-PROD-*)
│   ├── relationships.py            ← Relationships domain requirements (REQ-REL-*)
│   ├── learning.py                 ← Learning domain requirements (REQ-LEARN-*)
│   └── home.py                     ← Home domain requirements (REQ-HOME-*)
│
└── cassettes/                      ← Recorded LLM API responses for E2E replay
    └── .gitkeep
```

## Running Tests

### All tests (except drift)

```bash
pytest tests/ -v --ignore=tests/drift
```

### Unit tests only (fastest — < 2 seconds)

```bash
pytest tests/unit/ -v
```

### Integration tests

```bash
pytest tests/integration/ -v
```

### E2E tests (with cassettes)

```bash
pytest tests/e2e/ -v
```

### Drift tests (nightly, requires real LLM)

```bash
RUN_DRIFT_TESTS=1 OPENAI_API_KEY=sk-... pytest tests/drift/ -m drift -v
```

### Architecture tests

```bash
pytest tests/arch/ -v -s    # -s to see coverage reports
```

### Coverage report

```bash
pytest tests/ --cov=src --cov-report=html --ignore=tests/drift
```

## Test Tiers

| Tier | Speed | Dependencies | What It Proves |
|------|-------|-------------|----------------|
| **Unit** | ~1s | Mocks only | Logic is correct in isolation |
| **Integration** | ~5s | Real SQLite + mock Redis | Modules work together through real DB |
| **E2E** | ~10s | Cassettes (recorded LLM responses) | Full pipeline produces correct results |
| **Drift** | ~30s | Real gpt-4o-mini at temp=0 | Prompts still work with latest model version |
| **Arch** | ~2s | File system scan | Requirements have tests, domains have manifests |

## Tagging Tests with Requirements

Link tests to product requirements for traceability:

```python
@pytest.mark.req("REQ-HEALTH-001")
def test_meal_logging_extracts_food_items():
    ...

@pytest.mark.scenario("SCN-REQ-HEALTH-001-01")
def test_eggs_and_toast_triggers_log_meal():
    ...
```

Run the coverage report to see which requirements have tests:

```bash
pytest tests/arch/test_requirement_coverage.py -v -s
pytest tests/arch/test_scenario_generator.py -v -s
```

## Test Behaviour Coverage Matrix

### Platform Kernel (REQ-PLAT-*)

| ID | Requirement | Tests |
|----|------------|-------|
| REQ-PLAT-001 | Multi-Tenant Data Isolation | `unit/test_core/test_schemas.py` |
| REQ-PLAT-002 | Event Bus Decoupling | `unit/test_events/test_bus.py`, `integration/test_event_flow.py` |
| REQ-PLAT-003 | Three-Layer Memory System | `unit/test_memory/test_schemas.py` |
| REQ-PLAT-004 | Hybrid RAG Retrieval | `unit/test_retrieval/test_reranker.py`, `unit/test_retrieval/test_schemas.py` |
| REQ-PLAT-005 | Agent ReAct Loop | `unit/test_agents/test_registry.py`, `unit/test_agents/test_schemas.py` |
| REQ-PLAT-006 | Workflow Engine | `unit/test_orchestration/test_schemas.py` |
| REQ-PLAT-007 | Connector Framework | `unit/test_connectors/test_schemas.py` |
| REQ-PLAT-008 | Credential Encryption | `unit/test_shared/test_crypto.py` |
| REQ-PLAT-009 | Domain Plugin Architecture | `arch/test_domain_manifests.py` |

### Health Domain (REQ-HEALTH-*)

| ID | Requirement | Status |
|----|------------|--------|
| REQ-HEALTH-001 | Meal Logging via NLP | Phase 1 |
| REQ-HEALTH-002 | Exercise Logging | Phase 1 |
| REQ-HEALTH-003 | Sleep Logging | Phase 1 |
| REQ-HEALTH-004 | Nutrition Summary | Phase 1 |
| REQ-HEALTH-005 | Dietary Preference Memory | Phase 1 |
| REQ-HEALTH-006 | Health Goal Setting | Phase 1 |
| REQ-HEALTH-007 | Nutrition Coach Agent | Phase 1 |
| REQ-HEALTH-008 | Vitals Recording | Phase 1 |

### Finance Domain (REQ-FIN-*)

| ID | Requirement | Status |
|----|------------|--------|
| REQ-FIN-001 | Transaction Logging via NLP | Phase 1 |
| REQ-FIN-002 | Spending Summary | Phase 1 |
| REQ-FIN-003 | Budget Management | Phase 1 |
| REQ-FIN-004 | Financial Goal Setting | Phase 1 |
| REQ-FIN-005 | Budget Advisor Agent | Phase 1 |

### Productivity Domain (REQ-PROD-*)

| ID | Requirement | Status |
|----|------------|--------|
| REQ-PROD-001 | Task Creation via NLP | Phase 1 |
| REQ-PROD-002 | Task Completion | Phase 1 |
| REQ-PROD-003 | Task Listing | Phase 1 |
| REQ-PROD-004 | Habit Tracking | Phase 1 |
| REQ-PROD-005 | Daily Summary | Phase 1 |
| REQ-PROD-006 | Planner Agent | Phase 1 |

### Relationships Domain (REQ-REL-*)

| ID | Requirement | Status |
|----|------------|--------|
| REQ-REL-001 | Interaction Logging | Phase 1 |
| REQ-REL-002 | Contact Management | Phase 1 |
| REQ-REL-003 | Interaction History Query | Phase 1 |
| REQ-REL-004 | Important Date Reminders | Phase 1 |

### Learning Domain (REQ-LEARN-*)

| ID | Requirement | Status |
|----|------------|--------|
| REQ-LEARN-001 | Learning Resource Tracking | Phase 1 |
| REQ-LEARN-002 | Study Session Logging | Phase 1 |
| REQ-LEARN-003 | Learning Progress Query | Phase 1 |
| REQ-LEARN-004 | Note Capture | Phase 1 |
| REQ-LEARN-005 | AI Tutor Agent | Phase 1 |

### Home Domain (REQ-HOME-*)

| ID | Requirement | Status |
|----|------------|--------|
| REQ-HOME-001 | Household Task Management | Phase 1 |
| REQ-HOME-002 | Shopping List Management | Phase 1 |
| REQ-HOME-003 | Maintenance Scheduling | Phase 1 |
| REQ-HOME-004 | Household Manager Agent | Phase 1 |

## Cassette Workflow

### Record a new cassette

```bash
RECORD_CASSETTES=1 pytest tests/e2e/test_message_to_response.py -v
```

### Replay from cassette (default — CI mode)

```bash
pytest tests/e2e/ -v
```

### Re-record after prompt change

Delete the cassette file and re-run with `RECORD_CASSETTES=1`.

## CI Pipeline Recommendations

| Trigger | Tests Run | Duration |
|---------|-----------|----------|
| Every push | `pytest tests/unit/ tests/arch/` | ~3s |
| Pull request | `pytest tests/ --ignore=tests/drift` | ~15s |
| Merge to main | Full suite + coverage | ~20s |
| Nightly cron | `RUN_DRIFT_TESTS=1 pytest tests/drift/ -m drift` | ~30s |

## Adding a New Test

1. Create test file in the appropriate tier directory
2. Document each test function in the file docstring
3. Tag with `@pytest.mark.req("REQ-XXX-NNN")` if it covers a requirement
4. Tag with `@pytest.mark.scenario("SCN-REQ-XXX-NNN-NN")` if it covers a specific scenario
5. Run `pytest tests/arch/ -v -s` to verify coverage was recorded
