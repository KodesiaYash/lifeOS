"""
DomainPlugin protocol — the formal contract every domain must implement.

A domain author only needs to:
  1. Create a class that inherits DomainPlugin
  2. Implement the required methods
  3. Export it as `plugin` in the domain's __init__.py

The kernel's domain_loader will call these methods at startup to auto-wire
the domain into every platform layer (events, tools, agents, memory, routing).
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    from fastapi import APIRouter

    from src.events.schemas import PlatformEvent


# ---------------------------------------------------------------------------
# Data classes for domain declarations
# ---------------------------------------------------------------------------
@dataclass
class ToolDeclaration:
    """A tool the domain provides to the kernel."""

    tool_id: str  # e.g. "health.log_meal"
    name: str  # Human-readable name
    description: str  # Used in LLM tool descriptions
    handler: Callable  # Sync or async callable
    parameters_schema: dict = field(default_factory=dict)  # JSON Schema for args
    domain: str = ""  # Auto-set by loader


@dataclass
class AgentDeclaration:
    """An agent the domain provides."""

    agent_type: str  # e.g. "health.nutrition_coach"
    name: str
    description: str
    system_prompt: str  # The agent's personality/instructions
    tools: list[str] = field(default_factory=list)  # Tool IDs this agent can use
    model_preference: str | None = None  # Override default LLM model
    temperature: float = 0.7
    max_tokens: int = 2048
    domain: str = ""  # Auto-set by loader


@dataclass
class EventHandlerDeclaration:
    """An event the domain wants to subscribe to."""

    event_pattern: str  # Exact or wildcard, e.g. "health.*"
    handler: Callable[[PlatformEvent], Coroutine[Any, Any, None]]
    description: str = ""


@dataclass
class MemoryCategoryDeclaration:
    """A memory category the domain uses for structured facts."""

    category: str  # e.g. "dietary_preference"
    description: str  # What kind of facts go here
    example_keys: list[str] = field(default_factory=list)  # e.g. ["diet_type", "calorie_goal"]


@dataclass
class WorkflowDeclaration:
    """A workflow the domain provides."""

    workflow_id: str  # e.g. "health.weekly_review"
    name: str
    description: str
    trigger_type: str  # "schedule", "event", "manual"
    trigger_config: dict = field(default_factory=dict)
    steps: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# The plugin protocol
# ---------------------------------------------------------------------------
class DomainPlugin(abc.ABC):
    """
    Base class for all domain plugins.

    Subclass this, implement the abstract methods, and export as `plugin`
    in your domain's __init__.py. The kernel handles everything else.

    Layers wired automatically:
      ✓ Tool Registry    — tools you declare become callable by agents/LLM
      ✓ Agent Registry   — agents you declare are available for routing
      ✓ Event Bus        — your handlers get subscribed to event patterns
      ✓ Memory           — your categories are registered for structured facts
      ✓ Orchestration    — your workflows are loaded into the engine
      ✓ FastAPI Router   — your router is mounted under /api/v1/domains/{domain_id}
      ✓ Domain Registry  — your metadata is stored in the DB for domain activation
    """

    # ── Required metadata (override in subclass) ──────────────────────

    @property
    @abc.abstractmethod
    def domain_id(self) -> str:
        """Unique domain identifier, e.g. 'health'."""
        ...

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Human-readable name, e.g. 'Health & Fitness'."""
        ...

    @property
    @abc.abstractmethod
    def version(self) -> str:
        """Semantic version, e.g. '0.1.0'."""
        ...

    @property
    def description(self) -> str:
        """Optional longer description."""
        return ""

    # ── Layer declarations (override to provide) ──────────────────────

    def get_tools(self) -> list[ToolDeclaration]:
        """Return tools this domain provides. Default: none."""
        return []

    def get_agents(self) -> list[AgentDeclaration]:
        """Return agents this domain provides. Default: none."""
        return []

    def get_event_handlers(self) -> list[EventHandlerDeclaration]:
        """Return event subscriptions. Default: none."""
        return []

    def get_memory_categories(self) -> list[MemoryCategoryDeclaration]:
        """Return memory categories this domain uses. Default: none."""
        return []

    def get_workflows(self) -> list[WorkflowDeclaration]:
        """Return workflows this domain provides. Default: none."""
        return []

    def get_router(self) -> APIRouter | None:
        """Return a FastAPI router for domain-specific endpoints. Default: none."""
        return None

    # ── Lifecycle hooks ───────────────────────────────────────────────

    async def on_startup(self) -> None:  # noqa: B027
        """Called when the domain is loaded. Use for initialization."""
        pass

    async def on_shutdown(self) -> None:  # noqa: B027
        """Called when the app shuts down. Use for cleanup."""
        pass

    # ── Introspection (auto-generated, do not override) ───────────────

    def get_manifest(self) -> dict:
        """Generate a manifest dict from the plugin's declarations."""
        return {
            "domain_id": self.domain_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "event_types": [h.event_pattern for h in self.get_event_handlers()],
            "tools": [t.tool_id for t in self.get_tools()],
            "agents": [a.agent_type for a in self.get_agents()],
            "memory_categories": [m.category for m in self.get_memory_categories()],
            "workflows": [w.workflow_id for w in self.get_workflows()],
        }

    def validate(self) -> list[str]:
        """
        Validate the plugin's declarations. Returns list of error messages.
        Empty list = valid.
        """
        errors = []

        # Naming conventions
        for tool in self.get_tools():
            if not tool.tool_id.startswith(f"{self.domain_id}."):
                errors.append(f"Tool '{tool.tool_id}' must start with '{self.domain_id}.'")

        for agent in self.get_agents():
            if not agent.agent_type.startswith(f"{self.domain_id}."):
                errors.append(f"Agent '{agent.agent_type}' must start with '{self.domain_id}.'")

        # Agent tools must reference declared tools
        declared_tool_ids = {t.tool_id for t in self.get_tools()}
        for agent in self.get_agents():
            for tool_id in agent.tools:
                if tool_id not in declared_tool_ids:
                    errors.append(
                        f"Agent '{agent.agent_type}' references tool '{tool_id}' which is not declared in get_tools()"
                    )

        return errors
