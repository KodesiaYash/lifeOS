# Pending Work

> Include this file to know what's been done and what's next.

## Phase 0 — COMPLETE

All 18 steps done:

1. Project skeleton (pyproject.toml, Dockerfile, docker-compose.yml, .env.example, alembic)
2. Shared utilities (database, base_model, crypto, pagination, time)
3. Config & app entry (config.py, main.py with domain plugin loading, dependencies.py)
4. Core module (settings, domain registry) — **single-user mode with simplified global state**
5. Events module (event bus pub/sub, event log)
6. Communication module (WhatsApp/Telegram/REST adapters, conversations, messages)
7. Memory module (short-term Redis, structured SQL, semantic pgvector, assembler, consolidation)
8. Knowledge module (documents, chunks, ingestion pipeline, chunking, embedding, parsers, tagging)
9. Retrieval module (semantic/structured/keyword retrievers, reranker, coordinator)
10. Kernel module (LLM client via LiteLLM, prompt/tool registries, global orchestrator)
11. Orchestration module (workflow engine with step types)
12. Agents module (runtime with ReAct tool-calling, registry)
13. Scheduling module (APScheduler + arq worker)
14. Domain plugin system (DomainPlugin protocol, loader, 7 domains with dutch_tutor promoted)
15. Connectors scaffold (base connector, service, models)
16. Seed data script (scripts/seed.py)
17. Full test suite (unit/integration/e2e/drift/arch + requirements) — **335 tests passing**
18. Documentation (ARCHITECTURE.md, per-module READMEs, domain guide, tests README, LLM_CONTEXT.md)

## Phase 0.5 — CI/CD + DevOps (COMPLETE)

- ✅ GitHub Actions CI pipeline (`.github/workflows/ci.yml`)
- ✅ Jobs: lint, unit-tests, integration-tests, e2e-tests, arch-tests, migration-check, llm-connectivity
- ✅ Venv caching for faster builds
- ✅ Initial Alembic migration committed
- ✅ Pre-push script (`scripts/pre_push.sh`)
- ✅ LLM verification script (`scripts/verify_llm.py`)
- ✅ Multi-provider LLM config (OpenAI, Anthropic, Gemini, Groq, Mistral)
- ✅ pgAdmin + RedisInsight in docker-compose.yml

## Phase 1 — PENDING (Domain Implementations)

Replace stub handlers with real logic. Per domain:

### Health
- Real meal parsing (NLP → food items → calorie estimation)
- Exercise/sleep logging with structured storage
- Nutrition summaries with macro breakdowns
- Vitals recording and trend detection
- SQLAlchemy models: MealLog, ExerciseLog, SleepLog, VitalsRecord, HealthGoal

### Finance
- Transaction parsing from natural language
- Spending summaries with category breakdown
- Budget tracking with alerts
- Models: Transaction, Budget, FinancialGoal

### Productivity
- Task CRUD with NLP creation
- Habit tracking with streaks and reminders
- Daily/weekly summaries
- Models: Task, Habit, Project

### Relationships
- Contact management with enriched profiles
- Interaction logging (calls, messages, meetings)
- Important date reminders
- Models: Contact, Interaction, ImportantDate

### Learning
- Resource tracking (books, courses, articles)
- Session logging with progress tracking
- Note capture linked to resources
- RAG over learning materials
- Models: LearningResource, StudySession, LearningNote

### Home
- Household task management
- Shopping list CRUD
- Maintenance scheduling with recurrence
- Models: HouseholdTask, ShoppingList, MaintenanceSchedule

### Cross-Cutting Phase 1
- Intent classification: real LLM-based routing (message → domain → agent)
- Tag all existing tests with `@pytest.mark.req()` for full traceability
- Record E2E cassettes for real LLM interactions
- Alembic migrations for domain models
- ~~CI/CD pipeline setup (GitHub Actions)~~ ✅ DONE in Phase 0.5
