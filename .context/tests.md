# Test Suite Reference

> Include this file when writing tests, debugging test failures, or adding requirements.

## Test Tiers

| Tier | Dir | Speed | Dependencies | Purpose |
|------|-----|-------|-------------|---------|
| **Unit** | `tests/unit/` | ~1s | Mocks only | Isolated logic correctness |
| **Integration** | `tests/integration/` | ~5s | Real SQLite, mock Redis | Cross-module data flows |
| **E2E** | `tests/e2e/` | ~10s | Cassettes (recorded LLM) | Full user scenarios |
| **Drift** | `tests/drift/` | ~30s | Real gpt-4o-mini, temp=0 | Prompt/model regression |
| **Arch** | `tests/arch/` | ~2s | File system scan | Structure + coverage enforcement |

## Running Tests

```bash
pytest tests/unit/ -v                                          # Fastest
pytest tests/ -v --ignore=tests/drift                          # CI default
pytest tests/arch/ -v -s                                       # Domain wiring + coverage reports
RUN_DRIFT_TESTS=1 OPENAI_API_KEY=sk-... pytest tests/drift/   # Nightly
pytest tests/ --cov=src --cov-report=html --ignore=tests/drift # Coverage
```

## Requirement Tagging

```python
@pytest.mark.req("REQ-HEALTH-001")
@pytest.mark.scenario("SCN-REQ-HEALTH-001-01")
def test_meal_message_triggers_log_meal_tool():
    ...
```

Custom markers in `pyproject.toml`: `req(id)`, `scenario(id)`, `drift`.

## Architecture Tests

| File | What It Enforces |
|------|-----------------|
| `test_domain_integration.py` | Every domain wired into tools, agents, events, memory, router |
| `test_domain_manifests.py` | Domain files exist, manifests valid, naming correct |
| `test_requirement_coverage.py` | Every P0 requirement has ≥1 tagged test |
| `test_scenario_generator.py` | Acceptance criteria → scenarios → coverage check |

## Product Requirements (41 total)

- `tests/requirements/platform.py` — REQ-PLAT-001–009 (kernel)
- `tests/requirements/health.py` — REQ-HEALTH-001–008
- `tests/requirements/finance.py` — REQ-FIN-001–005
- `tests/requirements/productivity.py` — REQ-PROD-001–006
- `tests/requirements/relationships.py` — REQ-REL-001–004
- `tests/requirements/learning.py` — REQ-LEARN-001–005
- `tests/requirements/home.py` — REQ-HOME-001–004

## Key Test Files

- `tests/conftest.py` — Root: async event loop, in-memory SQLite, identity UUIDs
- `tests/unit/conftest.py` — Mock event bus, LLM client, DB, prompt/tool registries
- `tests/integration/conftest.py` — Real SQLite, mock Redis, mock embeddings
- `tests/e2e/conftest.py` — CassetteManager (record/replay LLM), mock LLM
- `tests/drift/conftest.py` — RUN_DRIFT_TESTS=1 gate, OPENAI_API_KEY required

## CI Pipeline

| Trigger | Command | Duration |
|---------|---------|----------|
| Every push | `pytest tests/unit/ tests/arch/` | ~3s |
| Pull request | `pytest tests/ --ignore=tests/drift` | ~15s |
| Merge to main | Full suite + coverage | ~20s |
| Nightly cron | `RUN_DRIFT_TESTS=1 pytest tests/drift/ -m drift` | ~30s |
