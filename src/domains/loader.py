"""
Domain loader — discovers and wires domain plugins into every platform layer.

Called once at application startup. For each domain plugin:
  1. Validates the plugin (naming conventions, tool references)
  2. Registers tools into the ToolRegistry
  3. Registers agents into the AgentRegistry
  4. Subscribes event handlers to the EventBus
  5. Registers memory categories (stored for reference)
  6. Loads workflows into the orchestration engine
  7. Mounts the domain's FastAPI router
  8. Calls the plugin's on_startup() lifecycle hook
  9. Logs the full wiring report
"""
from __future__ import annotations

import importlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

from src.agents.registry import AgentRegistry
from src.agents.schemas import AgentDefinitionRead
from src.domains.plugin import DomainPlugin
from src.events.bus import EventBus
from src.kernel.tool_registry import ToolDefinition, ToolRegistry

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = structlog.get_logger()

# All discovered and loaded plugins, keyed by domain_id
_loaded_plugins: dict[str, DomainPlugin] = {}

# Memory categories registered across all domains
_memory_categories: dict[str, list[dict]] = {}


def get_loaded_plugins() -> dict[str, DomainPlugin]:
    """Return all loaded domain plugins (read-only snapshot)."""
    return dict(_loaded_plugins)


def get_memory_categories() -> dict[str, list[dict]]:
    """Return all registered memory categories across domains."""
    return dict(_memory_categories)


def discover_domain_plugins() -> list[DomainPlugin]:
    """
    Discover all domain plugins by scanning src/domains/*/

    Each domain must export a `plugin` attribute in its __init__.py
    that is an instance of DomainPlugin.

    Domains without a `plugin` attribute are skipped (backward compat
    with manifest-only scaffolds).
    """
    domains_dir = Path(__file__).parent
    plugins = []

    for domain_dir in sorted(domains_dir.iterdir()):
        if not domain_dir.is_dir():
            continue
        if domain_dir.name.startswith("_"):
            continue
        if not (domain_dir / "__init__.py").exists():
            continue

        module_name = f"src.domains.{domain_dir.name}"
        try:
            mod = importlib.import_module(module_name)
        except ImportError as e:
            logger.warning("domain_import_error", domain=domain_dir.name, error=str(e))
            continue

        if hasattr(mod, "plugin") and isinstance(mod.plugin, DomainPlugin):
            plugins.append(mod.plugin)
        else:
            logger.debug("domain_no_plugin", domain=domain_dir.name,
                         hint="Add `plugin = MyDomainPlugin()` to __init__.py")

    return plugins


def _register_tools(plugin: DomainPlugin, tool_registry: ToolRegistry) -> int:
    """Register all tools from a plugin. Returns count registered."""
    count = 0
    for tool in plugin.get_tools():
        defn = ToolDefinition(
            tool_id=tool.tool_id,
            name=tool.name,
            description=tool.description,
            domain=plugin.domain_id,
            parameters_schema=tool.parameters_schema,
        )
        tool_registry.register(defn, tool.handler)
        count += 1
    return count


def _register_agents(plugin: DomainPlugin, agent_registry: AgentRegistry) -> int:
    """Register all agents from a plugin. Returns count registered."""
    count = 0
    for agent in plugin.get_agents():
        defn = AgentDefinitionRead(
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
            created_at=datetime.now(timezone.utc),
        )
        agent_registry.register(defn)
        count += 1
    return count


def _subscribe_events(plugin: DomainPlugin, event_bus: EventBus) -> int:
    """Subscribe all event handlers from a plugin. Returns count subscribed."""
    count = 0
    for handler_decl in plugin.get_event_handlers():
        event_bus.subscribe(handler_decl.event_pattern, handler_decl.handler)
        count += 1
    return count


def _register_memory_categories(plugin: DomainPlugin) -> int:
    """Register memory categories. Returns count registered."""
    cats = plugin.get_memory_categories()
    _memory_categories[plugin.domain_id] = [
        {"category": c.category, "description": c.description, "example_keys": c.example_keys}
        for c in cats
    ]
    return len(cats)


def _mount_router(plugin: DomainPlugin, app: "FastAPI") -> bool:
    """Mount the domain's router if provided. Returns True if mounted."""
    router = plugin.get_router()
    if router is not None:
        prefix = f"/api/v1/domains/{plugin.domain_id}"
        app.include_router(router, prefix=prefix, tags=[plugin.domain_id])
        return True
    return False


async def load_domain_plugins(
    app: "FastAPI",
    tool_registry: ToolRegistry,
    agent_registry: AgentRegistry,
    event_bus: EventBus,
) -> dict[str, dict]:
    """
    Main entry point — discover, validate, and wire all domain plugins.

    Returns a wiring report dict: {domain_id: {tools: N, agents: N, ...}}
    """
    plugins = discover_domain_plugins()
    report: dict[str, dict] = {}

    for plugin in plugins:
        domain_id = plugin.domain_id

        # Validate
        errors = plugin.validate()
        if errors:
            logger.error("domain_validation_failed", domain=domain_id, errors=errors)
            report[domain_id] = {"status": "failed", "errors": errors}
            continue

        # Wire into every layer
        tools_count = _register_tools(plugin, tool_registry)
        agents_count = _register_agents(plugin, agent_registry)
        events_count = _subscribe_events(plugin, event_bus)
        memory_count = _register_memory_categories(plugin)
        router_mounted = _mount_router(plugin, app)

        # Lifecycle hook
        await plugin.on_startup()

        # Store reference
        _loaded_plugins[domain_id] = plugin

        domain_report = {
            "status": "loaded",
            "version": plugin.version,
            "tools": tools_count,
            "agents": agents_count,
            "event_handlers": events_count,
            "memory_categories": memory_count,
            "router_mounted": router_mounted,
            "workflows": len(plugin.get_workflows()),
        }
        report[domain_id] = domain_report

        logger.info(
            "domain_loaded",
            domain=domain_id,
            **domain_report,
        )

    logger.info(
        "all_domains_loaded",
        total=len(report),
        successful=sum(1 for r in report.values() if r["status"] == "loaded"),
        failed=sum(1 for r in report.values() if r["status"] == "failed"),
    )

    return report
