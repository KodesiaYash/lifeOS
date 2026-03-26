"""
Integration test: Tool registry → Agent registry → invocation readiness.

Tests the wiring between tool registration, agent definition, and
the agent's ability to reference tools by ID.

Tests:
  - test_agent_tools_resolve_in_registry: Tools listed in agent definition exist in tool registry
  - test_domain_tools_match_agent_domain: Agent's domain tools are findable
  - test_tool_invoke_and_agent_reference: Tool invocation works for agent-listed tool IDs
  - test_unregistered_tool_graceful_fail: Agent referencing missing tool gets error result
"""

import uuid
from datetime import UTC, datetime

import pytest

from src.agents.registry import AgentRegistry
from src.agents.schemas import AgentDefinitionRead
from src.kernel.tool_registry import ToolDefinition, ToolRegistry


def _agent(agent_type: str, tools: list[str], domain: str = "health") -> AgentDefinitionRead:
    return AgentDefinitionRead(
        id=uuid.uuid4(),
        agent_type=agent_type,
        name=f"Agent {agent_type}",
        description="Test",
        domain=domain,
        system_prompt="You are a test agent.",
        model_preference=None,
        temperature=0.7,
        max_tokens=2048,
        tools=tools,
        capabilities={},
        active=True,
        version=1,
        created_at=datetime.now(UTC),
    )


class TestToolAgentFlow:
    """Integration: tool registry + agent registry wiring."""

    def setup_method(self):
        self.tools = ToolRegistry()
        self.agents = AgentRegistry()

    def test_agent_tools_resolve_in_registry(self):
        """
        Scenario: Agent declares tools=["health.log_meal", "health.get_summary"].
        Both tools must exist in the tool registry.
        """
        self.tools.register(
            ToolDefinition(tool_id="health.log_meal", name="Log Meal", description="Log", domain="health"),
            lambda **kw: {"logged": True},
        )
        self.tools.register(
            ToolDefinition(tool_id="health.get_summary", name="Summary", description="Get", domain="health"),
            lambda **kw: {"summary": "ok"},
        )

        agent = _agent("health.coach", tools=["health.log_meal", "health.get_summary"])
        self.agents.register(agent)

        for tool_id in agent.tools:
            assert self.tools.get(tool_id) is not None, f"Tool {tool_id} not found"

    def test_domain_tools_match_agent_domain(self):
        """
        Scenario: Agent has domain='health'.
        All tools with domain='health' should be available.
        """
        for i in range(3):
            self.tools.register(
                ToolDefinition(tool_id=f"health.t{i}", name=f"T{i}", description=f"D{i}", domain="health"),
                lambda: None,
            )
        self.tools.register(
            ToolDefinition(tool_id="finance.t0", name="FT", description="FD", domain="finance"),
            lambda: None,
        )

        health_tools = self.tools.list_tools(domain="health")
        assert len(health_tools) == 3

    @pytest.mark.asyncio
    async def test_tool_invoke_and_agent_reference(self):
        """
        Scenario: Agent references tool 'health.log_meal'.
        Invoking that tool through the registry returns a successful result.
        """
        self.tools.register(
            ToolDefinition(tool_id="health.log_meal", name="Log", description="Log meal", domain="health"),
            lambda meal: {"logged": True, "meal": meal},
        )

        result = await self.tools.invoke("health.log_meal", meal="breakfast")
        assert result.success is True
        assert result.data["meal"] == "breakfast"

    @pytest.mark.asyncio
    async def test_unregistered_tool_graceful_fail(self):
        """
        Scenario: Agent references a tool that doesn't exist.
        Invocation returns error result, not exception.
        """
        result = await self.tools.invoke("health.nonexistent_tool")
        assert result.success is False
        assert "not found" in result.error.lower()
