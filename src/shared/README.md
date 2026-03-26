# Shared Utilities (`src/shared/`)

Foundation utilities used by all other modules. This package has **zero dependencies** on any other `src/` module.

## Contents

| File | Purpose |
|------|---------|
| `database.py` | Async SQLAlchemy engine, session factory, `get_db` FastAPI dependency |
| `base_model.py` | `Base` declarative base and `TimestampedBase` with standard columns (id, created_at, updated_at, deleted_at) |
| `pagination.py` | `PaginationParams` and `PaginatedResult` for list endpoints |
| `crypto.py` | AES-256 encrypt/decrypt via Fernet (for connector credentials, secrets) |
| `time.py` | Timezone-aware datetime helpers (utc_now, to_user_tz, start/end of day) |

## Usage

```python
from src.shared.database import get_db
from src.shared.base_model import TimestampedBase
from src.shared.time import utc_now
```

## Design Rules

- **No imports from other `src/` modules** (except `src.config`).
- Everything here must be generic and reusable.
- No business logic — only infrastructure utilities.
