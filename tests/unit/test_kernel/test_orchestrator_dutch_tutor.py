"""Unit tests for Dutch tutor orchestration through the promoted domain flow."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from src.agents.registry import AgentRegistry
from src.agents.schemas import AgentDefinitionRead
from src.communication.schemas import ChannelType, ContentType
from src.config import settings
from src.domains.dutch_tutor import DutchTutorPlugin
from src.events.bus import EventBus
from src.kernel.orchestrator import GlobalOrchestrator, OrchestratorContext
from src.kernel.tool_registry import ToolDefinition, ToolRegistry
from src.memory.schemas import ScopedMemoryPacket
from src.retrieval.schemas import RetrievalResponse, RetrievalStrategy


def _mock_short_term() -> AsyncMock:
    short_term = AsyncMock()
    short_term.get_message_history = AsyncMock(return_value=[])
    short_term.add_to_message_history = AsyncMock()
    short_term.get_session = AsyncMock(return_value={})
    return short_term


def _mock_retrieval() -> AsyncMock:
    retrieval = AsyncMock()
    retrieval.retrieve = AsyncMock(
        return_value=RetrievalResponse(
            results=[],
            total_found=0,
            strategy_used=RetrievalStrategy.MEMORY_ONLY,
            query="",
        )
    )
    return retrieval


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
@pytest.mark.req("REQ-DUTCH-001")
@pytest.mark.scenario("SCN-REQ-PLAT-010-02")
@pytest.mark.asyncio
async def test_domain_process_assembles_scoped_memory_and_uses_direct_tool(mock_db_session):
    plugin = DutchTutorPlugin()
    plugin.capture_memory = AsyncMock()

    memory_service = AsyncMock()
    memory_service.retrieve_scoped_context = AsyncMock(
        return_value=ScopedMemoryPacket(namespace="dutch_tutor", general_namespace="general")
    )

    orchestrator = GlobalOrchestrator(
        mock_db_session,
        short_term=_mock_short_term(),
        retrieval=_mock_retrieval(),
        memory_service=memory_service,
        event_bus_instance=EventBus(),
        tool_registry_instance=_tool_registry_from_plugin(plugin),
        agent_registry_instance=_agent_registry_from_plugin(plugin),
        domain_plugins={plugin.domain_id: plugin},
    )

    ctx = OrchestratorContext(
        user_message="huis",
        channel_type=ChannelType.TELEGRAM,
        session_id="conv-1",
        bot_id=settings.DUTCH_TUTOR_BOT_ID,
        target_domain="dutch_tutor",
        user_name="Yash",
        content_type=ContentType.TEXT,
    )

    response = await orchestrator.process(ctx)

    assert response == "Nederlands: huis\nEnglish: house\nBack to Dutch: huis"
    plugin.capture_memory.assert_awaited_once()
    memory_service.retrieve_scoped_context.assert_awaited_once()
    assert ctx.intent is not None
    assert ctx.intent["domain"] == "dutch_tutor"
    assert ctx.intent["direct_tool"] == "dutch_tutor.translate_roundtrip"
    assert ctx.memory_context is not None
    assert ctx.memory_context["namespace"] == "dutch_tutor"


@pytest.mark.req("REQ-PLAT-010")
@pytest.mark.scenario("SCN-REQ-PLAT-010-03")
@pytest.mark.asyncio
async def test_domain_process_emits_lifecycle_events(mock_db_session):
    event_bus = EventBus()
    captured = []

    async def handler(event):
        captured.append(event)

    event_bus.subscribe("communication.message_received", handler)
    event_bus.subscribe("system.message_processed", handler)
    event_bus.subscribe("dutch_tutor.message_processed", handler)

    plugin = DutchTutorPlugin()
    plugin.capture_memory = AsyncMock()

    memory_service = AsyncMock()
    memory_service.retrieve_scoped_context = AsyncMock(
        return_value=ScopedMemoryPacket(namespace="dutch_tutor", general_namespace="general")
    )

    orchestrator = GlobalOrchestrator(
        mock_db_session,
        short_term=_mock_short_term(),
        retrieval=_mock_retrieval(),
        memory_service=memory_service,
        event_bus_instance=event_bus,
        tool_registry_instance=_tool_registry_from_plugin(plugin),
        agent_registry_instance=_agent_registry_from_plugin(plugin),
        domain_plugins={plugin.domain_id: plugin},
    )

    ctx = OrchestratorContext(
        user_message="boek",
        channel_type=ChannelType.TELEGRAM,
        session_id="conv-2",
        bot_id=settings.DUTCH_TUTOR_BOT_ID,
        target_domain="dutch_tutor",
        channel_user_id="999",
        external_chat_id="555",
        content_type=ContentType.TEXT,
    )

    await orchestrator.process(ctx)

    event_types = [event.event_type for event in captured]
    assert event_types == [
        "communication.message_received",
        "system.message_processed",
        "dutch_tutor.message_processed",
    ]
    correlation_ids = {event.correlation_id for event in captured}
    assert len(correlation_ids) == 1
