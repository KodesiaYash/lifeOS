# Events Module (`src/events/`)

In-process event bus with database persistence. Foundation for the platform's event-driven architecture.

## Contents

| File | Purpose |
|------|---------|
| `schemas.py` | `PlatformEvent` canonical event schema, `EventQuery` for filtering |
| `models.py` | SQLAlchemy model for `evt_events` table |
| `bus.py` | `EventBus` — in-process publish/subscribe with wildcard pattern matching |
| `repository.py` | Event persistence and query operations |
| `router.py` | GET `/api/v1/events/events` — query events with filters |

## Usage

```python
from src.events.bus import event_bus
from src.events.schemas import PlatformEvent

# Publish an event
event = PlatformEvent(
    tenant_id=tenant_id,
    user_id=user_id,
    event_type="health.meal_logged",
    domain="health",
    payload={"calories": 520},
)
await event_bus.publish(event, session=db)

# Subscribe to events
@event_bus.subscribe("health.*")
async def on_health_event(event: PlatformEvent):
    ...
```

## Design

- **Append-only**: Events are never modified or deleted.
- **In-process dispatch**: No external message broker needed for MVP.
- **Wildcard subscriptions**: `"health.*"` matches all health domain events.
- **Persistence optional**: Events can be published without DB persistence for transient signals.
