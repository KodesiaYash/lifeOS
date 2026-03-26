"""
Database access layer for events.

Single-user mode: No tenant_id or user_id filtering.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.events.models import Event
from src.events.schemas import EventQuery, PlatformEvent


class EventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def persist(self, event: PlatformEvent) -> Event:
        """Persist a PlatformEvent to the database."""
        db_event = Event(
            id=event.id,
            event_type=event.event_type,
            event_category=event.event_category,
            domain=event.domain,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            payload=event.payload,
            metadata_=event.metadata,
            source=event.source,
            importance=event.importance,
            timestamp=event.timestamp,
        )
        self.session.add(db_event)
        await self.session.flush()
        return db_event

    async def query(self, query: EventQuery) -> list[Event]:
        """Query events with filters."""
        stmt = select(Event)

        if query.event_type is not None:
            stmt = stmt.where(Event.event_type == query.event_type)
        if query.domain is not None:
            stmt = stmt.where(Event.domain == query.domain)
        if query.correlation_id is not None:
            stmt = stmt.where(Event.correlation_id == query.correlation_id)
        if query.since is not None:
            stmt = stmt.where(Event.timestamp >= query.since)
        if query.until is not None:
            stmt = stmt.where(Event.timestamp <= query.until)

        stmt = stmt.order_by(Event.timestamp.desc()).offset(query.offset).limit(query.limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_correlation_id(self, correlation_id: uuid.UUID) -> list[Event]:
        """Get all events in a correlation chain."""
        result = await self.session.execute(
            select(Event).where(Event.correlation_id == correlation_id).order_by(Event.timestamp.asc())
        )
        return list(result.scalars().all())
