# Conventions & Gotchas

> Include this file to remind any LLM of the project's rules and common pitfalls.

## Naming Rules (enforced by arch tests)

| Item | Pattern | Example |
|------|---------|---------|
| Tool ID | `{domain}.{action}` | `health.log_meal` |
| Agent type | `{domain}.{role}` | `health.nutrition_coach` |
| Event type | `{domain}.{past_tense}` | `health.meal_logged` |
| Requirement ID | `REQ-{DOMAIN}-{NNN}` | `REQ-HEALTH-001` |
| Scenario ID | `SCN-REQ-{DOMAIN}-{NNN}-{NN}` | `SCN-REQ-HEALTH-001-01` |

## Important Rules

1. **All tool handlers must be async** — `async def _log_meal(**kwargs):`
2. **All identifiers namespaced with domain** — `health.log_meal`, never `log_meal`
3. **Every domain exports `plugin = MyPlugin()`** as the last line of `__init__.py`
4. **Requirements are Python dicts** in `tests/requirements/`, not Markdown docs
5. **Each test file has a module docstring** listing every test function
6. **Stubs return** `{"status": "stub", "action": "...", "input": kwargs}`
7. **Static manifest.py and plugin declarations must stay in sync** — arch tests verify
8. **EventBus uses `_handlers` internally** — NOT `_subscribers`
9. **No flat test files** — everything in `tests/{tier}/test_{module}/`
10. **Cassettes for E2E, real LLM for drift** — never real LLM in CI except nightly

## Common Gotchas

- **Forgetting `plugin = MyPlugin()`** → domain won't be discovered by loader
- **Sync handler on a tool** → arch test fails, would block the event loop at runtime
- **Agent references undeclared tool** → `validate()` fails, arch test catches it
- **Event pattern without domain prefix** → arch test fails
- **Memory category without example_keys** → arch test fails
- **Importing `_subscribers` from EventBus** → doesn't exist, it's `_handlers`

## Code Style

- Logging: `structlog` (JSON in prod, console in dev)
- Config: `pydantic-settings` via `src/config.py`
- Schemas: Pydantic v2 `BaseModel`
- DB models: SQLAlchemy 2.0 async (declarative base in `src/shared/base_model.py`)
- Encryption: Fernet symmetric via `src/shared/crypto.py`
- Linting: `ruff` (configured in `pyproject.toml`)
- Type checking: `mypy` (configured in `pyproject.toml`)
