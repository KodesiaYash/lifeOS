"""
API endpoints for event querying.

Single-user mode: No tenant/user context required.
"""
import uuid
from datetime import datetime

from fastapi import APIRouter, Query

from src.dependencies import DbSession
from src.events.repository import EventRepository
from src.events.schemas import EventQuery, PlatformEvent

router = APIRouter()


@router.get("/events", response_model=list[PlatformEvent])
async def list_events(
    db: DbSession,
    event_type: str | None = Query(default=None),
    domain: str | None = Query(default=None),
    correlation_id: uuid.UUID | None = Query(default=None),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[PlatformEvent]:
    repo = EventRepository(db)
    query = EventQuery(
        event_type=event_type,
        domain=domain,
        correlation_id=correlation_id,
        since=since,
        until=until,
        limit=limit,
        offset=offset,
    )
    events = await repo.query(query)
    return [
        PlatformEvent(
            id=e.id,
            event_type=e.event_type,
            event_category=e.event_category,
            domain=e.domain,
            correlation_id=e.correlation_id,
            causation_id=e.causation_id,
            payload=e.payload,
            metadata=e.metadata_,
            source=e.source,
            importance=e.importance,
            timestamp=e.timestamp,
        )
        for e in events
    ]
