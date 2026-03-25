"""
Architecture test: Verify every domain plugin is properly wired into ALL platform layers.

This is the "domain health check" — it instantiates each plugin and verifies that:
  1. Plugin class is valid (inherits DomainPlugin, passes validate())
  2. Tools layer: Every declared tool has a callable handler with correct naming
  3. Agents layer: Every agent references only declared tools
  4. Events layer: Every event handler has a valid pattern and callable handler
  5. Memory layer: Every memory category has description and example keys
  6. Router layer: Plugin provides a FastAPI router
  7. Cross-layer: Tools in agents exist in tool declarations (no dangling references)
  8. Manifest consistency: Generated manifest matches static manifest.py

This test ensures a domain author ONLY needs to:
  - Subclass DomainPlugin
  - Implement get_tools(), get_agents(), get_event_handlers(), get_memory_categories(), get_router()
  - Export `plugin = MyPlugin()` in __init__.py
  ...and the kernel handles ALL wiring automatically.

Tests:
  - test_plugin_discoverable: Each domain exports a `plugin` attribute
  - test_plugin_validates: validate() returns no errors
  - test_tools_layer_complete: Every tool has handler, description, and correct prefix
  - test_agents_layer_complete: Every agent has system_prompt, and all tool refs are valid
  - test_events_layer_complete: Every event handler has callable and pattern
  - test_memory_layer_complete: Every memory category has description and examples
  - test_router_layer_provided: Plugin provides a FastAPI router
  - test_cross_layer_tool_references: No agent references a tool that isn't declared
  - test_manifest_consistency: Plugin's get_manifest() matches static manifest.py
  - test_full_wiring_simulation: Simulate the domain loader wiring all layers
  - test_domain_health_report: Print full integration health report (informational)
"""
import importlib
import inspect
from pathlib import Path

import pytest

from src.domains.plugin import DomainPlugin

DOMAINS = ["health", "finance", "productivity", "relationships", "learning", "home"]
DOMAINS_DIR = Path(__file__).parent.parent.parent / "src" / "domains"


def _load_plugin(domain: str) -> DomainPlugin | None:
    """Import the domain module and return its `plugin` attribute."""
    mod = importlib.import_module(f"src.domains.{domain}")
    return getattr(mod, "plugin", None)


# ---------------------------------------------------------------------------
# Layer 0: Plugin Discovery
# ---------------------------------------------------------------------------
class TestPluginDiscovery:
    """Verify every domain exports a valid DomainPlugin instance."""

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_plugin_discoverable(self, domain):
        """Each domain __init__.py must export `plugin` as a DomainPlugin instance."""
        plugin = _load_plugin(domain)
        assert plugin is not None, f"src/domains/{domain}/__init__.py missing `plugin = ...`"
        assert isinstance(plugin, DomainPlugin), (
            f"{domain} plugin is {type(plugin).__name__}, expected DomainPlugin subclass"
        )

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_plugin_validates(self, domain):
        """Plugin.validate() must return no errors (naming, tool refs, etc.)."""
        plugin = _load_plugin(domain)
        errors = plugin.validate()
        assert errors == [], f"{domain} plugin validation failed:\n" + "\n".join(errors)

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_plugin_metadata(self, domain):
        """Plugin has domain_id, name, version, description."""
        plugin = _load_plugin(domain)
        assert plugin.domain_id == domain
        assert len(plugin.name) > 0
        assert len(plugin.version) > 0


# ---------------------------------------------------------------------------
# Layer 1: Tools
# ---------------------------------------------------------------------------
class TestToolsLayer:
    """Verify every domain's tools are complete and callable."""

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_tools_exist(self, domain):
        """Every domain must declare at least 1 tool."""
        plugin = _load_plugin(domain)
        tools = plugin.get_tools()
        assert len(tools) >= 1, f"{domain} has no tools"

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_tools_have_handlers(self, domain):
        """Every tool must have a callable handler."""
        plugin = _load_plugin(domain)
        for tool in plugin.get_tools():
            assert callable(tool.handler), (
                f"Tool {tool.tool_id} handler is not callable: {tool.handler}"
            )

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_tools_naming_convention(self, domain):
        """Every tool_id must start with 'domain.'."""
        plugin = _load_plugin(domain)
        for tool in plugin.get_tools():
            assert tool.tool_id.startswith(f"{domain}."), (
                f"Tool '{tool.tool_id}' must start with '{domain}.'"
            )

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_tools_have_description(self, domain):
        """Every tool must have a non-empty description (used in LLM tool call)."""
        plugin = _load_plugin(domain)
        for tool in plugin.get_tools():
            assert len(tool.description) > 10, (
                f"Tool {tool.tool_id} description too short: '{tool.description}'"
            )

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_tool_handlers_are_async(self, domain):
        """Tool handlers should be async for non-blocking execution."""
        plugin = _load_plugin(domain)
        for tool in plugin.get_tools():
            assert inspect.iscoroutinefunction(tool.handler), (
                f"Tool {tool.tool_id} handler should be async"
            )


# ---------------------------------------------------------------------------
# Layer 2: Agents
# ---------------------------------------------------------------------------
class TestAgentsLayer:
    """Verify every domain's agents are complete and reference valid tools."""

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_agents_exist(self, domain):
        """Every domain must declare at least 1 agent."""
        plugin = _load_plugin(domain)
        agents = plugin.get_agents()
        assert len(agents) >= 1, f"{domain} has no agents"

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_agents_have_system_prompt(self, domain):
        """Every agent must have a system prompt (personality/instructions)."""
        plugin = _load_plugin(domain)
        for agent in plugin.get_agents():
            assert len(agent.system_prompt) > 20, (
                f"Agent {agent.agent_type} system_prompt too short"
            )

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_agents_naming_convention(self, domain):
        """Every agent_type must start with 'domain.'."""
        plugin = _load_plugin(domain)
        for agent in plugin.get_agents():
            assert agent.agent_type.startswith(f"{domain}."), (
                f"Agent '{agent.agent_type}' must start with '{domain}.'"
            )

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_agents_reference_declared_tools(self, domain):
        """
        CROSS-LAYER CHECK: Every tool_id in agent.tools must exist in get_tools().
        This prevents dangling tool references that would fail at runtime.
        """
        plugin = _load_plugin(domain)
        declared_tool_ids = {t.tool_id for t in plugin.get_tools()}
        for agent in plugin.get_agents():
            for tool_id in agent.tools:
                assert tool_id in declared_tool_ids, (
                    f"Agent {agent.agent_type} references tool '{tool_id}' "
                    f"which is not declared in get_tools(). "
                    f"Available: {declared_tool_ids}"
                )

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_agents_have_at_least_one_tool(self, domain):
        """Every agent should have at least one tool assigned."""
        plugin = _load_plugin(domain)
        for agent in plugin.get_agents():
            assert len(agent.tools) >= 1, (
                f"Agent {agent.agent_type} has no tools — it can't do anything useful"
            )


# ---------------------------------------------------------------------------
# Layer 3: Events
# ---------------------------------------------------------------------------
class TestEventsLayer:
    """Verify every domain's event handlers are complete."""

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_event_handlers_exist(self, domain):
        """Every domain should declare at least 1 event handler."""
        plugin = _load_plugin(domain)
        handlers = plugin.get_event_handlers()
        assert len(handlers) >= 1, f"{domain} has no event handlers"

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_event_handlers_are_callable(self, domain):
        """Every event handler must be an async callable."""
        plugin = _load_plugin(domain)
        for h in plugin.get_event_handlers():
            assert callable(h.handler), f"Handler for {h.event_pattern} is not callable"
            assert inspect.iscoroutinefunction(h.handler), (
                f"Handler for {h.event_pattern} must be async"
            )

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_event_patterns_namespaced(self, domain):
        """Event patterns must be namespaced with 'domain.' or 'domain.*'."""
        plugin = _load_plugin(domain)
        for h in plugin.get_event_handlers():
            assert h.event_pattern.startswith(f"{domain}."), (
                f"Event pattern '{h.event_pattern}' must start with '{domain}.'"
            )


# ---------------------------------------------------------------------------
# Layer 4: Memory
# ---------------------------------------------------------------------------
class TestMemoryLayer:
    """Verify every domain declares memory categories."""

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_memory_categories_exist(self, domain):
        """Every domain should declare at least 1 memory category."""
        plugin = _load_plugin(domain)
        cats = plugin.get_memory_categories()
        assert len(cats) >= 1, f"{domain} has no memory categories"

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_memory_categories_have_description(self, domain):
        """Every memory category must have a description."""
        plugin = _load_plugin(domain)
        for cat in plugin.get_memory_categories():
            assert len(cat.description) > 5, (
                f"Memory category '{cat.category}' needs a description"
            )

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_memory_categories_have_examples(self, domain):
        """Every memory category must have at least 1 example key."""
        plugin = _load_plugin(domain)
        for cat in plugin.get_memory_categories():
            assert len(cat.example_keys) >= 1, (
                f"Memory category '{cat.category}' needs at least 1 example_key"
            )


# ---------------------------------------------------------------------------
# Layer 5: Router
# ---------------------------------------------------------------------------
class TestRouterLayer:
    """Verify every domain provides a FastAPI router."""

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_router_provided(self, domain):
        """Plugin.get_router() must return a non-None APIRouter."""
        plugin = _load_plugin(domain)
        router = plugin.get_router()
        assert router is not None, f"{domain} get_router() returned None"
        # Verify it's an actual APIRouter
        from fastapi import APIRouter
        assert isinstance(router, APIRouter), (
            f"{domain} get_router() returned {type(router).__name__}, expected APIRouter"
        )


# ---------------------------------------------------------------------------
# Layer 6: Manifest Consistency
# ---------------------------------------------------------------------------
class TestManifestConsistency:
    """Verify plugin's generated manifest matches static manifest.py."""

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_manifest_tools_match(self, domain):
        """Tools in plugin.get_manifest() match tools in manifest.py."""
        plugin = _load_plugin(domain)
        generated = plugin.get_manifest()

        static_mod = importlib.import_module(f"src.domains.{domain}.manifest")
        static = static_mod.MANIFEST

        gen_tools = set(generated["tools"])
        static_tools = set(static["tools"])

        # Generated must be a superset of (or equal to) static manifest
        missing = static_tools - gen_tools
        assert not missing, (
            f"{domain}: manifest.py declares tools {missing} not in plugin.get_tools()"
        )

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_manifest_agents_match(self, domain):
        """Agents in plugin.get_manifest() match agents in manifest.py."""
        plugin = _load_plugin(domain)
        generated = plugin.get_manifest()

        static_mod = importlib.import_module(f"src.domains.{domain}.manifest")
        static = static_mod.MANIFEST

        gen_agents = set(generated["agents"])
        static_agents = set(static["agents"])

        missing = static_agents - gen_agents
        assert not missing, (
            f"{domain}: manifest.py declares agents {missing} not in plugin.get_agents()"
        )


# ---------------------------------------------------------------------------
# Full Wiring Simulation
# ---------------------------------------------------------------------------
class TestFullWiringSimulation:
    """Simulate the domain loader wiring each plugin into kernel registries."""

    @pytest.mark.asyncio
    async def test_all_domains_wire_into_tool_registry(self):
        """All domain tools register into a shared ToolRegistry without collision."""
        from src.kernel.tool_registry import ToolRegistry
        registry = ToolRegistry()

        all_tool_ids = set()
        for domain in DOMAINS:
            plugin = _load_plugin(domain)
            for tool in plugin.get_tools():
                assert tool.tool_id not in all_tool_ids, (
                    f"Tool ID collision: {tool.tool_id}"
                )
                all_tool_ids.add(tool.tool_id)
                from src.kernel.tool_registry import ToolDefinition
                registry.register(
                    ToolDefinition(
                        tool_id=tool.tool_id, name=tool.name,
                        description=tool.description, domain=plugin.domain_id,
                        parameters_schema=tool.parameters_schema,
                    ),
                    tool.handler,
                )

        # All tools should be findable
        for tool_id in all_tool_ids:
            assert registry.get(tool_id) is not None

        # Domain filtering should work
        for domain in DOMAINS:
            domain_tools = registry.list_tools(domain=domain)
            assert len(domain_tools) >= 1

    @pytest.mark.asyncio
    async def test_all_domains_wire_into_agent_registry(self):
        """All domain agents register into a shared AgentRegistry."""
        import uuid
        from datetime import datetime, timezone
        from src.agents.registry import AgentRegistry
        from src.agents.schemas import AgentDefinitionRead

        registry = AgentRegistry()
        all_agent_types = set()

        for domain in DOMAINS:
            plugin = _load_plugin(domain)
            for agent in plugin.get_agents():
                assert agent.agent_type not in all_agent_types, (
                    f"Agent type collision: {agent.agent_type}"
                )
                all_agent_types.add(agent.agent_type)
                registry.register(AgentDefinitionRead(
                    id=uuid.uuid4(), agent_type=agent.agent_type,
                    name=agent.name, description=agent.description,
                    domain=plugin.domain_id, system_prompt=agent.system_prompt,
                    model_preference=agent.model_preference,
                    temperature=agent.temperature, max_tokens=agent.max_tokens,
                    tools=agent.tools, capabilities={}, active=True, version=1,
                    created_at=datetime.now(timezone.utc),
                ))

        # All agents findable
        for agent_type in all_agent_types:
            assert registry.get(agent_type) is not None

        # Domain filtering
        for domain in DOMAINS:
            domain_agents = registry.list_agents(domain=domain)
            assert len(domain_agents) >= 1

    @pytest.mark.asyncio
    async def test_all_domains_wire_into_event_bus(self):
        """All domain event handlers subscribe to the event bus."""
        from src.events.bus import EventBus

        bus = EventBus()
        total_handlers = 0

        for domain in DOMAINS:
            plugin = _load_plugin(domain)
            for h in plugin.get_event_handlers():
                bus.subscribe(h.event_pattern, h.handler)
                total_handlers += 1

        assert total_handlers >= len(DOMAINS), (
            f"Expected at least {len(DOMAINS)} handlers, got {total_handlers}"
        )

    @pytest.mark.asyncio
    async def test_tool_invocation_after_wiring(self):
        """After wiring, every tool is invocable through the registry."""
        from src.kernel.tool_registry import ToolDefinition, ToolRegistry

        registry = ToolRegistry()
        for domain in DOMAINS:
            plugin = _load_plugin(domain)
            for tool in plugin.get_tools():
                registry.register(
                    ToolDefinition(
                        tool_id=tool.tool_id, name=tool.name,
                        description=tool.description, domain=plugin.domain_id,
                    ),
                    tool.handler,
                )

        # Invoke one tool from each domain
        for domain in DOMAINS:
            plugin = _load_plugin(domain)
            first_tool = plugin.get_tools()[0]
            result = await registry.invoke(first_tool.tool_id)
            assert result.success is True, (
                f"Failed to invoke {first_tool.tool_id}: {result.error}"
            )


# ---------------------------------------------------------------------------
# Health Report (informational)
# ---------------------------------------------------------------------------
class TestDomainHealthReport:
    """Print a per-domain integration health report."""

    def test_domain_health_report(self):
        """Informational: prints the domain → layer integration matrix."""
        print("\n" + "=" * 80)
        print("DOMAIN INTEGRATION HEALTH REPORT")
        print("=" * 80)

        for domain in DOMAINS:
            plugin = _load_plugin(domain)
            errors = plugin.validate()
            tools = plugin.get_tools()
            agents = plugin.get_agents()
            events = plugin.get_event_handlers()
            memory = plugin.get_memory_categories()
            router = plugin.get_router()

            status = "✓ HEALTHY" if not errors else f"✗ {len(errors)} ERROR(S)"
            print(f"\n── {domain.upper()} ({plugin.version}) — {status} ──")
            print(f"  Tools:    {len(tools):2d}  {[t.tool_id for t in tools]}")
            print(f"  Agents:   {len(agents):2d}  {[a.agent_type for a in agents]}")
            print(f"  Events:   {len(events):2d}  {[e.event_pattern for e in events]}")
            print(f"  Memory:   {len(memory):2d}  {[m.category for m in memory]}")
            print(f"  Router:   {'✓' if router else '✗'}")

            if errors:
                for e in errors:
                    print(f"  ⚠ {e}")

        # Summary
        print("\n" + "-" * 80)
        total_tools = sum(len(_load_plugin(d).get_tools()) for d in DOMAINS)
        total_agents = sum(len(_load_plugin(d).get_agents()) for d in DOMAINS)
        total_events = sum(len(_load_plugin(d).get_event_handlers()) for d in DOMAINS)
        total_memory = sum(len(_load_plugin(d).get_memory_categories()) for d in DOMAINS)
        print(f"TOTAL: {len(DOMAINS)} domains, {total_tools} tools, "
              f"{total_agents} agents, {total_events} event handlers, "
              f"{total_memory} memory categories")
        print("=" * 80)
