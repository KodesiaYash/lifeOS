"""
Integration test: Event bus → handler → side effect chain.

Verifies that publishing an event triggers subscribed handlers across modules
and that wildcard subscriptions work in a multi-handler scenario.

Tests:
  - test_event_triggers_multiple_handlers: Single event fires all matching handlers
  - test_wildcard_routes_to_domain_handler: domain.* catches all domain events
  - test_correlation_id_propagates: correlation_id survives from publish to handler
  - test_handler_receives_full_payload: Complex nested payload is intact in handler
"""
import uuid

import pytest

from src.events.bus import EventBus
from src.events.schemas import PlatformEvent


def _event(event_type: str, payload: dict | None = None, correlation_id=None) -> PlatformEvent:
    return PlatformEvent(
        tenant_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        event_type=event_type,
        event_category=event_type.split(".")[0],
        payload=payload or {},
        source="integration_test",
        correlation_id=correlation_id,
    )


class TestEventFlow:
    """Integration: event bus dispatch across multiple subscribers."""

    @pytest.mark.asyncio
    async def test_event_triggers_multiple_handlers(self):
        """
        Scenario: health.meal_logged is published.
        Two handlers subscribe: memory updater + goal checker.
        Both must fire.
        """
        bus = EventBus()
        memory_calls = []
        goal_calls = []

        async def memory_handler(event, session=None):
            memory_calls.append(event.event_type)

        async def goal_handler(event, session=None):
            goal_calls.append(event.event_type)

        bus.subscribe("health.meal_logged", memory_handler)
        bus.subscribe("health.meal_logged", goal_handler)

        await bus.publish(_event("health.meal_logged", {"calories": 350}))

        assert len(memory_calls) == 1
        assert len(goal_calls) == 1

    @pytest.mark.asyncio
    async def test_wildcard_routes_to_domain_handler(self):
        """
        Scenario: health.* wildcard catches meal_logged, exercise_logged, sleep_logged.
        finance.tx_logged must NOT be caught.
        """
        bus = EventBus()
        health_events = []

        async def health_handler(event, session=None):
            health_events.append(event.event_type)

        bus.subscribe("health.*", health_handler)

        for et in ["health.meal_logged", "health.exercise_logged", "health.sleep_logged", "finance.tx_logged"]:
            await bus.publish(_event(et))

        assert len(health_events) == 3
        assert "finance.tx_logged" not in health_events

    @pytest.mark.asyncio
    async def test_correlation_id_propagates(self):
        """
        Scenario: A message triggers a chain of events, all sharing the same correlation_id.
        Handler must see the original correlation_id.
        """
        bus = EventBus()
        received_cid = []

        async def handler(event, session=None):
            received_cid.append(event.correlation_id)

        bus.subscribe("test.corr", handler)

        cid = uuid.uuid4()
        await bus.publish(_event("test.corr", correlation_id=cid))

        assert received_cid[0] == cid

    @pytest.mark.asyncio
    async def test_handler_receives_full_payload(self):
        """
        Scenario: Event carries a complex nested payload (meal with items, macros).
        Handler receives the full structure intact.
        """
        bus = EventBus()
        captured = []

        async def handler(event, session=None):
            captured.append(event.payload)

        bus.subscribe("health.meal_logged", handler)

        payload = {
            "meal_type": "breakfast",
            "items": [
                {"name": "eggs", "quantity": 2, "calories": 140},
                {"name": "toast", "quantity": 1, "calories": 80},
            ],
            "total_calories": 220,
            "macros": {"protein": 18, "carbs": 15, "fat": 10},
        }
        await bus.publish(_event("health.meal_logged", payload))

        assert captured[0]["items"][0]["name"] == "eggs"
        assert captured[0]["macros"]["protein"] == 18
