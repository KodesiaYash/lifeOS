# Development Changelog

> Session-by-session history of what was built. Update this at the end of each development session.

---

## Session 1 — Phase 0 Foundation (2026-03-24)

**Built the entire kernel foundation (18 steps):**

- Project skeleton: pyproject.toml, Dockerfile, docker-compose.yml, .env.example, alembic
- All 12 platform modules: shared, core, events, communication, memory, knowledge, retrieval, kernel, orchestration, agents, scheduling, connectors
- Domain scaffolds for 6 domains (health, finance, productivity, relationships, learning, home) — simple __init__.py with DOMAIN_ID/NAME/VERSION + manifest.py + router.py + models.py + README.md
- Seed script, per-module READMEs, global README
- Initial flat test files (7 files): test_shared, test_events, test_knowledge, test_retrieval, test_kernel, test_agents, test_schemas

## Session 2 — Test Architecture + Product Requirements (2026-03-24/25)

**Restructured tests into 5-tier architecture:**

- Moved flat test files into `tests/unit/test_{module}/` directories (15 test files)
- Created tier-specific conftest files: unit, integration, e2e, drift
- Integration tests: test_event_flow.py, test_knowledge_flow.py, test_tool_agent_flow.py
- E2E tests: CassetteManager conftest + test_message_to_response.py
- Drift tests: RUN_DRIFT_TESTS gate + test_intent_classification.py (6 real-LLM tests)

**Product requirements as code:**

- Created `tests/requirements/` with 7 files: platform.py (9 reqs), health.py (8), finance.py (5), productivity.py (6), relationships.py (4), learning.py (5), home.py (4) = 41 total
- Arch tests: test_requirement_coverage.py, test_domain_manifests.py, test_scenario_generator.py

**Domain plugin system:**

- Created `src/domains/plugin.py` — DomainPlugin ABC with ToolDeclaration, AgentDeclaration, EventHandlerDeclaration, MemoryCategoryDeclaration, WorkflowDeclaration
- Created `src/domains/loader.py` — discover_domain_plugins(), load_domain_plugins() with 9-step auto-wiring
- Updated all 6 domain __init__.py files to implement DomainPlugin with full tool/agent/event/memory declarations and stub handlers
- Created `tests/arch/test_domain_integration.py` — comprehensive all-layer verification (discovery, tools, agents, events, memory, router, cross-layer, manifest, wiring simulation)
- Wired loader into `src/main.py` lifespan — registries stored on app.state

**Documentation:**

- Created `ARCHITECTURE.md` — product-driven ideology, 3 pillars, system layers, requirement flow
- Created `src/domains/README.md` — domain developer guide with templates and step-by-step
- Updated `tests/README.md` — added product-driven testing philosophy section
- Updated `README.md` — running tests section, design documents links
- Created `LLM_CONTEXT.md` — monolithic context for LLM handoff

**Contextual development system:**

- Created `.context/` module with manifest.yml + chunked topic files
- Files: manifest.yml, overview.md, architecture.md, domains.md, tests.md, conventions.md, pending.md, changelog.md, TODO.md, README.md
