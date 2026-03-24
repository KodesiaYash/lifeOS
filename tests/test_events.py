"""
Tests for the events module.
"""
import asyncio
import uuid

import pytest
import pytest_asyncio

from src.events.bus import EventBus
from src.events.schemas import PlatformEvent


class TestEventBus:
    def test_subscribe_and_list(self):
        bus = EventBus()
        handler_called = False

        async def handler(event, session=None):
            nonlocal handler_called
            handler_called = True

        bus.subscribe("test.event", handler)
        assert "test.event" in bus._subscribers
        assert len(bus._subscribers["test.event"]) == 1

    def test_subscribe_wildcard(self):
        bus = EventBus()

        async def handler(event, session=None):
            pass

        bus.subscribe("test.*", handler)
        assert "test.*" in bus._subscribers

    @pytest.mark.asyncio
    async def test_publish_calls_handler(self):
        bus = EventBus()
        received_events = []

        async def handler(event, session=None):
            received_events.append(event)

        bus.subscribe("test.event", handler)

        event = PlatformEvent(
            tenant_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            event_type="test.event",
            event_category="test",
            payload={"key": "value"},
            source="test",
        )
        await bus.publish(event)

        assert len(received_events) == 1
        assert received_events[0].event_type == "test.event"

    @pytest.mark.asyncio
    async def test_publish_wildcard_match(self):
        bus = EventBus()
        received = []

        async def handler(event, session=None):
            received.append(event.event_type)

        bus.subscribe("test.*", handler)

        for etype in ["test.one", "test.two", "other.event"]:
            event = PlatformEvent(
                tenant_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                event_type=etype,
                event_category="test",
                payload={},
                source="test",
            )
            await bus.publish(event)

        assert "test.one" in received
        assert "test.two" in received
        assert "other.event" not in received


class TestPlatformEvent:
    def test_event_creation(self):
        event = PlatformEvent(
            tenant_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            event_type="health.meal_logged",
            event_category="health",
            payload={"meal": "lunch"},
            source="user",
        )
        assert event.id is not None
        assert event.event_type == "health.meal_logged"
        assert event.payload["meal"] == "lunch"

    def test_event_correlation_id(self):
        cid = uuid.uuid4()
        event = PlatformEvent(
            tenant_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            event_type="test.event",
            event_category="test",
            correlation_id=cid,
            payload={},
            source="test",
        )
        assert event.correlation_id == cid
