"""Integration tests for the promoted Dutch tutor domain message flow."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from src.agents.registry import AgentRegistry
from src.agents.schemas import AgentDefinitionRead
from src.communication.pipeline import InboundMessagePipeline
from src.communication.repository import MessageRepository
from src.communication.schemas import ChannelType, ContentType, DeliveryReceipt, NormalizedInboundEvent
from src.config import settings
from src.domains.dutch_tutor import DutchTutorPlugin
from src.events.bus import EventBus
from src.kernel.orchestrator import GlobalOrchestrator
from src.kernel.tool_registry import ToolDefinition, ToolRegistry
from src.memory.short_term import ShortTermMemory
from src.retrieval.schemas import RetrievalResponse, RetrievalStrategy


class _PersistCheckOrchestrator:
    def __init__(self, session) -> None:
        self.session = session
        self.called = False

    async def process(self, ctx):
        self.called = True
        messages = await MessageRepository(self.session).list_by_conversation(ctx.conversation_id)
        inbound = [message for message in messages if message.direction == "inbound"]
        assert len(inbound) == 1
        assert inbound[0].body == "huis"
        assert ctx.target_domain == "dutch_tutor"
        return "Nederlands: huis\nEnglish: house\nBack to Dutch: huis"


def _tool_registry_from_plugin(plugin: DutchTutorPlugin) -> ToolRegistry:
    registry = ToolRegistry()
    for tool in plugin.get_tools():
        registry.register(
            ToolDefinition(
                tool_id=tool.tool_id,
                name=tool.name,
                description=tool.description,
                domain=plugin.domain_id,
                parameters_schema=tool.parameters_schema,
            ),
            tool.handler,
        )
    return registry


def _agent_registry_from_plugin(plugin: DutchTutorPlugin) -> AgentRegistry:
    registry = AgentRegistry()
    agent = plugin.get_agents()[0]
    registry.register(
        AgentDefinitionRead(
            id=uuid.uuid4(),
            agent_type=agent.agent_type,
            name=agent.name,
            description=agent.description,
            domain=plugin.domain_id,
            system_prompt=agent.system_prompt,
            model_preference=agent.model_preference,
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
            tools=agent.tools,
            capabilities={},
            active=True,
            version=1,
            created_at=datetime.now(UTC),
        )
    )
    return registry


@pytest.mark.req("REQ-PLAT-010")
@pytest.mark.scenario("SCN-REQ-PLAT-010-01")
@pytest.mark.asyncio
async def test_pipeline_persists_inbound_before_orchestration(session, channel_account):
    orchestrator = _PersistCheckOrchestrator(session)
    dispatcher = AsyncMock(return_value=DeliveryReceipt(channel_message_id="tg-1", status="sent"))
    pipeline = InboundMessagePipeline(
        session,
        orchestrator=orchestrator,
        dispatcher=dispatcher,
        event_bus_instance=EventBus(),
    )

    result = await pipeline.handle(
        channel_account_id=channel_account.id,
        event=NormalizedInboundEvent(
            channel_type=ChannelType.TELEGRAM,
            channel_user_id="999",
            external_chat_id="555",
            content_type=ContentType.TEXT,
            text="huis",
            idempotency_key="telegram:555:1",
        ),
        bot_id=settings.DUTCH_TUTOR_BOT_ID,
        target_domain="dutch_tutor",
        user_name="Yash",
    )

    assert orchestrator.called is True
    assert result.status == "processed"
    assert result.domain == "dutch_tutor"


@pytest.mark.req("REQ-PLAT-010")
@pytest.mark.req("REQ-DUTCH-001")
@pytest.mark.scenario("SCN-REQ-PLAT-010-03")
@pytest.mark.scenario("SCN-REQ-PLAT-010-04")
@pytest.mark.scenario("SCN-REQ-DUTCH-001-04")
@pytest.mark.asyncio
async def test_pipeline_emits_events_and_persists_roundtrip_translation(session, channel_account, mock_redis):
    event_bus = EventBus()
    captured = []

    async def handler(event):
        captured.append(event)

    for event_type in [
        "communication.message_received",
        "system.message_processed",
        "dutch_tutor.message_processed",
        "communication.message_sent",
    ]:
        event_bus.subscribe(event_type, handler)

    plugin = DutchTutorPlugin()
    retrieval = AsyncMock()
    retrieval.retrieve = AsyncMock(
        return_value=RetrievalResponse(
            results=[],
            total_found=0,
            strategy_used=RetrievalStrategy.MEMORY_ONLY,
            query="",
        )
    )

    orchestrator = GlobalOrchestrator(
        session,
        short_term=ShortTermMemory(redis=mock_redis),
        retrieval=retrieval,
        event_bus_instance=event_bus,
        tool_registry_instance=_tool_registry_from_plugin(plugin),
        agent_registry_instance=_agent_registry_from_plugin(plugin),
        domain_plugins={plugin.domain_id: plugin},
    )
    dispatcher = AsyncMock(return_value=DeliveryReceipt(channel_message_id="tg-2", status="sent"))
    pipeline = InboundMessagePipeline(
        session,
        orchestrator=orchestrator,
        dispatcher=dispatcher,
        event_bus_instance=event_bus,
    )

    result = await pipeline.handle(
        channel_account_id=channel_account.id,
        event=NormalizedInboundEvent(
            channel_type=ChannelType.TELEGRAM,
            channel_user_id="999",
            external_chat_id="555",
            content_type=ContentType.TEXT,
            text="huis",
            idempotency_key="telegram:555:2",
        ),
        bot_id=settings.DUTCH_TUTOR_BOT_ID,
        target_domain="dutch_tutor",
        user_name="Yash",
    )

    messages = await MessageRepository(session).list_by_conversation(uuid.UUID(result.conversation_id))
    outbound = [message for message in messages if message.direction == "outbound"]

    assert result.status == "processed"
    assert result.domain == "dutch_tutor"
    assert dispatcher.await_count == 1
    assert len(outbound) == 1
    assert outbound[0].body == "Nederlands: huis\nEnglish: house\nBack to Dutch: huis"
    assert outbound[0].channel_message_id == "tg-2"

    event_types = [event.event_type for event in captured]
    assert event_types == [
        "communication.message_received",
        "system.message_processed",
        "dutch_tutor.message_processed",
        "communication.message_sent",
    ]
    correlation_ids = {event.correlation_id for event in captured}
    assert len(correlation_ids) == 1
