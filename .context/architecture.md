# Architecture & Domain Plugin System

> Include this file when working on domain plugins, the loader, or kernel wiring.

## Domain Plugin Protocol

Every domain implements `DomainPlugin` from `src/domains/plugin.py`:

```python
class HealthPlugin(DomainPlugin):
    domain_id = "health"

    def get_tools(self) -> list[ToolDeclaration]                    # LLM-callable functions
    def get_agents(self) -> list[AgentDeclaration]                  # AI personalities
    def get_event_handlers(self) -> list[EventHandlerDeclaration]   # React to events
    def get_memory_categories(self) -> list[MemoryCategoryDeclaration]  # Fact types
    def get_router(self) -> APIRouter                               # HTTP endpoints
```

Last line of `__init__.py`: `plugin = HealthPlugin()`

## Auto-Wiring at Startup

`src/domains/loader.py` runs at app startup (called from `main.py` lifespan):

1. Scan `src/domains/*/` for `plugin` attribute
2. Validate naming conventions + tool references
3. Register tools → `ToolRegistry` (on `app.state.tool_registry`)
4. Register agents → `AgentRegistry` (on `app.state.agent_registry`)
5. Subscribe event handlers → `EventBus` (on `app.state.event_bus`)
6. Register memory categories
7. Mount router at `/api/v1/domains/{domain_id}`
8. Call `plugin.on_startup()`
9. Log wiring report

## Key Internal APIs

### EventBus (`src/events/bus.py`)
- Internal: `_handlers` dict (NOT `_subscribers`)
- Wildcard: `health.*` matches `health.meal_logged`
- Handler errors caught, don't block others
- Singleton: `event_bus`

### ToolRegistry (`src/kernel/tool_registry.py`)
- `register(ToolDefinition, callable)`, `get(tool_id)`, `invoke(tool_id, **kw)` → `ToolResult`
- Auto-detects sync/async via `inspect.iscoroutinefunction`
- `get_openai_tools(domain=)` — OpenAI function-calling format
- `list_tools(domain=)` — filter by domain

### AgentRegistry (`src/agents/registry.py`)
- `register(AgentDefinitionRead)`, `get(agent_type)`, `list_agents(domain=)`

### Memory System
- **Short-term:** Redis with TTL (session context)
- **Structured:** SQL facts with category, key, value, confidence
- **Semantic:** pgvector embeddings for fuzzy recall
- **MemoryPacket:** Combined output for prompt injection

## Naming Conventions (enforced by arch tests)

- Tools: `{domain}.{action}` → `health.log_meal`
- Agents: `{domain}.{role}` → `health.nutrition_coach`
- Events: `{domain}.{event}` → `health.meal_logged`
- Stubs return: `{"status": "stub", "action": "...", "input": kwargs}`
