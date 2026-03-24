# Core Module (`src/core/`)

Multi-tenant core entities: tenants, users, tenant-user links, workspaces, user profiles, and domain registry.

## Contents

| File | Purpose |
|------|---------|
| `models.py` | SQLAlchemy models: Tenant, User, TenantUser, Workspace, UserProfile, DomainRegistry, DomainInstallation |
| `schemas.py` | Pydantic request/response schemas for all core entities |
| `repository.py` | Database access layer (CRUD operations) |
| `service.py` | Business logic (create tenant, add user to tenant, create workspace) |
| `middleware.py` | Tenant context middleware — binds tenant_id to structlog context |
| `router.py` | FastAPI endpoints: `/api/v1/core/tenants`, `/api/v1/core/users`, `/api/v1/core/workspaces` |

## Key Design Decisions

- **Tenants and Users are global** — they exist outside tenant scope. `core_tenants` and `core_users` have no `tenant_id`.
- **TenantUser is the join** — links users to tenants with a role.
- **DomainRegistry is global** — tracks available domain plugins. DomainInstallation is tenant-scoped.
- **RLS is set at the DB session level** via `app.current_tenant_id`, not in middleware.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/core/tenants` | Create a tenant |
| GET | `/api/v1/core/tenants/{id}` | Get a tenant |
| POST | `/api/v1/core/users` | Create a user |
| GET | `/api/v1/core/users/{id}` | Get a user |
| POST | `/api/v1/core/tenants/{id}/users` | Add user to tenant |
| POST | `/api/v1/core/workspaces` | Create workspace (requires X-Tenant-Id) |
