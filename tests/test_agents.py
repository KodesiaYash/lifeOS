"""
Tests for the agents module.
"""
import pytest

from src.agents.registry import AgentRegistry
from src.agents.schemas import AgentDefinitionRead, AgentInvokeRequest
import uuid
from datetime import datetime, timezone


class TestAgentRegistry:
    def setup_method(self):
        self.registry = AgentRegistry()

    def _make_definition(self, agent_type: str, domain: str | None = None) -> AgentDefinitionRead:
        return AgentDefinitionRead(
            id=uuid.uuid4(),
            agent_type=agent_type,
            name=f"Agent {agent_type}",
            description=f"Test agent {agent_type}",
            domain=domain,
            system_prompt="You are a test agent.",
            model_preference=None,
            temperature=0.7,
            max_tokens=2048,
            tools=[],
            capabilities={},
            active=True,
            version=1,
            created_at=datetime.now(timezone.utc),
        )

    def test_register_and_get(self):
        defn = self._make_definition("test.agent")
        self.registry.register(defn)
        result = self.registry.get("test.agent")
        assert result is not None
        assert result.agent_type == "test.agent"

    def test_get_nonexistent(self):
        assert self.registry.get("nonexistent") is None

    def test_list_agents(self):
        self.registry.register(self._make_definition("a", "health"))
        self.registry.register(self._make_definition("b", "finance"))
        self.registry.register(self._make_definition("c", "health"))
        assert len(self.registry.list_agents()) == 3
        assert len(self.registry.list_agents(domain="health")) == 2

    def test_list_agent_types(self):
        self.registry.register(self._make_definition("x"))
        self.registry.register(self._make_definition("y"))
        assert sorted(self.registry.list_agent_types()) == ["x", "y"]

    def test_unregister(self):
        self.registry.register(self._make_definition("removable"))
        assert self.registry.get("removable") is not None
        self.registry.unregister("removable")
        assert self.registry.get("removable") is None


class TestAgentSchemas:
    def test_invoke_request(self):
        req = AgentInvokeRequest(
            agent_type="health.nutrition_coach",
            input_text="Log my breakfast: 2 eggs and toast",
        )
        assert req.agent_type == "health.nutrition_coach"
        assert req.context == {}
        assert req.correlation_id is None

    def test_invoke_request_with_context(self):
        cid = uuid.uuid4()
        req = AgentInvokeRequest(
            agent_type="test.agent",
            input_text="Hello",
            context={"key": "value"},
            correlation_id=cid,
        )
        assert req.context["key"] == "value"
        assert req.correlation_id == cid
