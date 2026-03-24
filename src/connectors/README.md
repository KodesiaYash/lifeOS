# Connectors Module (`src/connectors/`)

External service integration framework with encrypted credentials and sync logging.

## Contents

| File | Purpose |
|------|---------|
| `models.py` | SQLAlchemy models: ConnectorDefinition, ConnectorInstance, SyncLog |
| `schemas.py` | Pydantic schemas for connector CRUD |
| `repository.py` | Database access for connector entities |
| `base.py` | `BaseConnector` ABC — interface for all connector implementations |
| `service.py` | `ConnectorService` — install, configure, sync, and manage connectors |

## Connector Lifecycle

1. **Define**: Register connector type with auth_type and config_schema
2. **Install**: User creates an instance with credentials (encrypted at rest)
3. **Sync**: Periodic or manual sync fetches data from external service
4. **Log**: Every sync operation is logged with record counts and status

## Auth Types

- `oauth2` — OAuth 2.0 flow (Google, Fitbit, etc.)
- `api_key` — Static API key
- `basic` — Username/password
- `webhook` — Incoming webhooks only

## Planned Connectors

- Google Calendar, Google Fit
- Fitbit, Apple Health
- Todoist, Notion
- Bank APIs (Plaid)
- Smart home (Home Assistant)
