# Core Module (`src/core/`)

Core platform entities for single-user mode: settings and domain registry.

## Contents

| File | Purpose |
|------|---------|
| `models.py` | SQLAlchemy models: Settings, DomainRegistry |
| `schemas.py` | Pydantic request/response schemas for settings and domains |
| `repository.py` | Database access layer (CRUD operations) |
| `service.py` | Business logic (settings management, domain registration) |
| `middleware.py` | Request context middleware — binds request_id to structlog context |
| `router.py` | FastAPI endpoints for settings and domains |

## Key Design Decisions

- **Single-user mode** — no multi-tenancy, no user management needed
- **Settings** — key-value store for app configuration (timezone, language, theme)
- **DomainRegistry** — tracks available domain plugins and their manifests

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/core/settings` | Get all settings |
| PUT | `/api/v1/core/settings/{key}` | Update a setting |
| GET | `/api/v1/core/domains` | List registered domains |
| GET | `/api/v1/core/domains/{id}` | Get domain details |
