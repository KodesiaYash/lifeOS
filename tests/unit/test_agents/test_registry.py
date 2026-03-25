"""
Unit tests for src/agents/registry.py — in-memory agent definition registry.

Tests:
  - test_register_and_get: Register agent, retrieve by type
  - test_get_nonexistent: Missing type returns None
  - test_list_all_agents: Lists all registered agents
  - test_list_agents_by_domain: Domain filtering works
  - test_list_agent_types: Returns list of type ID strings
  - test_unregister: Removes agent from registry
  - test_overwrite_replaces: Re-registering same type overwrites
"""
import uuid
from datetime import datetime, timezone

from src.agents.registry import AgentRegistry
from src.agents.schemas import AgentDefinitionRead


def _defn(agent_type: str, domain: str | None = None) -> AgentDefinitionRead:
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


class TestAgentRegistry:
    """Verify in-memory agent registry CRUD."""

    def setup_method(self):
        self.registry = AgentRegistry()

    def test_register_and_get(self):
        """Registered agent is retrievable by type."""
        self.registry.register(_defn("test.agent"))
        result = self.registry.get("test.agent")
        assert result is not None
        assert result.agent_type == "test.agent"

    def test_get_nonexistent(self):
        """Missing type returns None."""
        assert self.registry.get("nope") is None

    def test_list_all_agents(self):
        """list_agents() returns all registered."""
        self.registry.register(_defn("a", "health"))
        self.registry.register(_defn("b", "finance"))
        self.registry.register(_defn("c", "health"))
        assert len(self.registry.list_agents()) == 3

    def test_list_agents_by_domain(self):
        """Domain filter narrows results."""
        self.registry.register(_defn("a", "health"))
        self.registry.register(_defn("b", "finance"))
        self.registry.register(_defn("c", "health"))
        assert len(self.registry.list_agents(domain="health")) == 2
        assert len(self.registry.list_agents(domain="finance")) == 1

    def test_list_agent_types(self):
        """Returns sorted list of type strings."""
        self.registry.register(_defn("x"))
        self.registry.register(_defn("y"))
        assert sorted(self.registry.list_agent_types()) == ["x", "y"]

    def test_unregister(self):
        """unregister() removes agent from registry."""
        self.registry.register(_defn("removable"))
        assert self.registry.get("removable") is not None
        self.registry.unregister("removable")
        assert self.registry.get("removable") is None

    def test_overwrite_replaces(self):
        """Re-registering same type overwrites the previous definition."""
        self.registry.register(_defn("ow"))
        new = _defn("ow", domain="new_domain")
        self.registry.register(new)
        assert self.registry.get("ow").domain == "new_domain"
