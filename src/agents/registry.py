"""
In-memory agent registry for fast lookup of agent definitions.
Complements the database-backed AgentDefinitionRepository.
"""
import structlog

from src.agents.schemas import AgentDefinitionRead

logger = structlog.get_logger()


class AgentRegistry:
    """
    In-memory registry of agent definitions.
    Loaded from the database at startup, used for fast routing.
    """

    def __init__(self) -> None:
        self._agents: dict[str, AgentDefinitionRead] = {}

    def register(self, definition: AgentDefinitionRead) -> None:
        """Register an agent definition."""
        self._agents[definition.agent_type] = definition
        logger.debug("agent_registered", agent_type=definition.agent_type, domain=definition.domain)

    def get(self, agent_type: str) -> AgentDefinitionRead | None:
        """Get an agent definition by type."""
        return self._agents.get(agent_type)

    def list_agents(self, domain: str | None = None) -> list[AgentDefinitionRead]:
        """List all registered agents, optionally filtered by domain."""
        agents = list(self._agents.values())
        if domain is not None:
            agents = [a for a in agents if a.domain == domain]
        return agents

    def list_agent_types(self) -> list[str]:
        """List all registered agent type IDs."""
        return list(self._agents.keys())

    def unregister(self, agent_type: str) -> None:
        """Remove an agent from the registry."""
        self._agents.pop(agent_type, None)


# Singleton registry
agent_registry = AgentRegistry()
