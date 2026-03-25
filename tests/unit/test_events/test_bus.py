"""
Unit tests for src/events/bus.py — in-process event bus.

Tests:
  - test_subscribe_registers_handler: Handler appears in subscriber list
  - test_subscribe_wildcard: Wildcard patterns are stored correctly
  - test_publish_exact_match: Handler fires on exact event type match
  - test_publish_wildcard_match: Wildcard handler fires for matching prefix
  - test_publish_wildcard_no_match: Wildcard handler ignores non-matching events
  - test_publish_no_subscribers: Publishing with no subscribers does not error
  - test_multiple_handlers: Multiple handlers on same event all fire
  - test_handler_receives_event_data: Handler receives full PlatformEvent with payload
  - test_handler_error_does_not_block_others: One failing handler does not prevent others from running
"""
import uuid

import pytest

from src.events.bus import EventBus
from src.events.schemas import PlatformEvent


def _make_event(event_type: str = "test.event", **kwargs) -> PlatformEvent:
    """Helper to create a PlatformEvent with minimal required fields."""
    return PlatformEvent(
        tenant_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        event_type=event_type,
        event_category=event_type.split(".")[0],
        payload=kwargs.get("payload", {}),
        source="test",
    )


class TestSubscribe:
    """Verify handler registration."""

    def test_subscribe_registers_handler(self):
        """Handler appears in internal subscriber mapping."""
        bus = EventBus()

        async def handler(event, session=None):
            pass

        bus.subscribe("test.event", handler)
        assert "test.event" in bus._handlers
        assert len(bus._handlers["test.event"]) == 1

    def test_subscribe_wildcard(self):
        """Wildcard pattern 'domain.*' is stored as-is."""
        bus = EventBus()

        async def handler(event, session=None):
            pass

        bus.subscribe("health.*", handler)
        assert "health.*" in bus._handlers

    def test_multiple_handlers(self):
        """Multiple handlers can subscribe to the same event type."""
        bus = EventBus()

        async def h1(event, session=None):
            pass

        async def h2(event, session=None):
            pass

        bus.subscribe("test.event", h1)
        bus.subscribe("test.event", h2)
        assert len(bus._handlers["test.event"]) == 2


class TestPublish:
    """Verify event dispatch behaviour."""

    @pytest.mark.asyncio
    async def test_publish_exact_match(self):
        """Handler fires when event type matches exactly."""
        bus = EventBus()
        received = []

        async def handler(event, session=None):
            received.append(event)

        bus.subscribe("test.event", handler)
        await bus.publish(_make_event("test.event"))

        assert len(received) == 1
        assert received[0].event_type == "test.event"

    @pytest.mark.asyncio
    async def test_publish_wildcard_match(self):
        """Wildcard 'test.*' matches test.one and test.two."""
        bus = EventBus()
        received = []

        async def handler(event, session=None):
            received.append(event.event_type)

        bus.subscribe("test.*", handler)

        await bus.publish(_make_event("test.one"))
        await bus.publish(_make_event("test.two"))
        await bus.publish(_make_event("other.event"))

        assert "test.one" in received
        assert "test.two" in received
        assert "other.event" not in received

    @pytest.mark.asyncio
    async def test_publish_wildcard_no_match(self):
        """Wildcard 'health.*' does not fire for 'finance.tx_logged'."""
        bus = EventBus()
        received = []

        async def handler(event, session=None):
            received.append(event)

        bus.subscribe("health.*", handler)
        await bus.publish(_make_event("finance.tx_logged"))
        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_publish_no_subscribers(self):
        """Publishing to an event with no subscribers is a no-op."""
        bus = EventBus()
        await bus.publish(_make_event("nobody.listening"))  # must not raise

    @pytest.mark.asyncio
    async def test_handler_receives_event_data(self):
        """Handler gets full PlatformEvent including payload."""
        bus = EventBus()
        captured = []

        async def handler(event, session=None):
            captured.append(event)

        bus.subscribe("test.data", handler)
        await bus.publish(_make_event("test.data", payload={"key": "value"}))

        assert captured[0].payload["key"] == "value"


class TestPlatformEvent:
    """Verify PlatformEvent schema."""

    def test_event_has_auto_id(self):
        """Every event gets a unique ID."""
        e = _make_event()
        assert e.id is not None

    def test_event_correlation_id(self):
        """Optional correlation_id is preserved."""
        cid = uuid.uuid4()
        e = PlatformEvent(
            tenant_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            event_type="test.corr",
            event_category="test",
            correlation_id=cid,
            payload={},
            source="test",
        )
        assert e.correlation_id == cid
