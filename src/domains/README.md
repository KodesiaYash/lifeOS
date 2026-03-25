# Domain Plugin System — Developer Guide

This document explains how to build a domain plugin for AI Life OS. A domain is a self-contained life area (health, finance, productivity, etc.) that plugs into the platform kernel.

**The contract:** you implement one Python class. The kernel handles everything else.

---

## What a Domain Provides

A domain plugin declares five things:

| Layer | Method | What you declare | What the kernel does with it |
|-------|--------|-----------------|------------------------------|
| **Tools** | `get_tools()` | Functions the LLM can call | Registers in ToolRegistry, exposes to agents via OpenAI function-calling format |
| **Agents** | `get_agents()` | AI personalities with system prompts | Registers in AgentRegistry, routes user messages to the right agent by intent |
| **Events** | `get_event_handlers()` | Reactions to platform events | Subscribes to EventBus, fires your handler when matching events are published |
| **Memory** | `get_memory_categories()` | Structured fact types | Registers categories so the memory assembler knows what facts exist per domain |
| **Router** | `get_router()` | HTTP endpoints | Mounts under `/api/v1/domains/{domain_id}` in the FastAPI app |

---

## Anatomy of a Domain Plugin

```
src/domains/health/
├── __init__.py       ← Plugin class + tool/event handlers + `plugin = HealthPlugin()`
├── manifest.py       ← Static manifest (tools, agents, events as string lists)
├── models.py         ← SQLAlchemy models (Phase 1)
├── router.py         ← FastAPI router with domain-specific endpoints
└── README.md         ← Domain-specific documentation
```

### The Plugin Class

```python
# src/domains/health/__init__.py

from src.domains.plugin import (
    AgentDeclaration, DomainPlugin, EventHandlerDeclaration,
    MemoryCategoryDeclaration, ToolDeclaration,
)

class HealthPlugin(DomainPlugin):

    @property
    def domain_id(self) -> str:
        return "health"

    @property
    def name(self) -> str:
        return "Health & Fitness"

    @property
    def version(self) -> str:
        return "0.1.0"

    def get_tools(self) -> list[ToolDeclaration]:
        return [
            ToolDeclaration(
                tool_id="health.log_meal",
                name="Log Meal",
                description="Log a meal with food items...",
                handler=_log_meal,          # async def _log_meal(**kw): ...
                parameters_schema={...},     # JSON Schema for LLM
            ),
            # ... more tools
        ]

    def get_agents(self) -> list[AgentDeclaration]:
        return [
            AgentDeclaration(
                agent_type="health.nutrition_coach",
                name="Nutrition Coach",
                description="Logs meals and provides nutrition advice.",
                system_prompt="You are a friendly nutrition coach...",
                tools=["health.log_meal", "health.get_nutrition_summary"],
            ),
        ]

    def get_event_handlers(self) -> list[EventHandlerDeclaration]:
        return [
            EventHandlerDeclaration(
                event_pattern="health.meal_logged",
                handler=_on_meal_logged,
                description="Update daily totals on meal log.",
            ),
        ]

    def get_memory_categories(self) -> list[MemoryCategoryDeclaration]:
        return [
            MemoryCategoryDeclaration(
                category="dietary_preference",
                description="User's dietary preferences (vegetarian, vegan, etc.)",
                example_keys=["diet_type", "meal_preference"],
            ),
        ]

    def get_router(self):
        from src.domains.health.router import router
        return router

# THIS LINE IS REQUIRED — the loader imports it
plugin = HealthPlugin()
```

---

## Step-by-Step: Creating a New Domain

### 1. Define product requirements

Create `tests/requirements/{domain}.py`:

```python
REQUIREMENTS = [
    {
        "id": "REQ-MYDOMAIN-001",
        "title": "My Feature",
        "description": "What it does...",
        "acceptance_criteria": [
            "When user says X, tool Y is called",
            "Response includes Z",
        ],
        "priority": "P0",
        "test_ids": [],
    },
]
```

### 2. Create the domain directory

```
src/domains/mydomain/
├── __init__.py      ← Plugin class (see template above)
├── manifest.py      ← Static manifest dict
├── models.py        ← SQLAlchemy models (can be empty initially)
├── router.py        ← FastAPI router (at least a /status endpoint)
└── README.md        ← Domain documentation
```

### 3. Implement the plugin class

Start with stub handlers that return `{"status": "stub", ...}`. This lets the entire wiring work from day one — tools are callable, agents reference them, events subscribe. Replace stubs with real implementations in Phase 1.

```python
async def _my_tool(**kwargs):
    """Stub: replace with real implementation."""
    return {"status": "stub", "action": "my_tool", "input": kwargs}
```

### 4. Create the static manifest

```python
# src/domains/mydomain/manifest.py
MANIFEST = {
    "domain_id": "mydomain",
    "name": "My Domain",
    "version": "0.1.0",
    "description": "...",
    "event_types": ["mydomain.something_happened"],
    "tools": ["mydomain.do_something"],
    "agents": ["mydomain.advisor"],
    "memory_categories": ["my_category"],
    "workflows": [],
}
```

### 5. Export the plugin singleton

The last line of `__init__.py` must be:

```python
plugin = MyDomainPlugin()
```

The domain loader discovers this attribute automatically.

### 6. Write tests

Tag tests with the requirement ID:

```python
@pytest.mark.req("REQ-MYDOMAIN-001")
@pytest.mark.scenario("SCN-REQ-MYDOMAIN-001-01")
def test_my_feature():
    ...
```

### 7. Run arch tests to verify wiring

```bash
pytest tests/arch/test_domain_integration.py -v -s
pytest tests/arch/test_domain_manifests.py -v -s
```

The arch tests will verify:
- Plugin is discoverable and valid
- All tools have async callable handlers with correct naming
- All agents reference only declared tools (no dangling refs)
- All event handlers have valid patterns and callables
- All memory categories have descriptions and example keys
- Router is provided and is a FastAPI APIRouter
- Generated manifest matches static manifest.py

---

## Naming Conventions

All identifiers must be namespaced with the domain ID:

| Item | Pattern | Example |
|------|---------|---------|
| Tool ID | `{domain}.{action}` | `health.log_meal` |
| Agent type | `{domain}.{role}` | `health.nutrition_coach` |
| Event type | `{domain}.{event}` | `health.meal_logged` |
| Memory category | `{category_name}` | `dietary_preference` |

The `validate()` method on `DomainPlugin` enforces these conventions. If a tool ID doesn't start with `{domain}.`, the plugin fails validation and won't load.

---

## Declaration Data Classes

### ToolDeclaration

```python
@dataclass
class ToolDeclaration:
    tool_id: str              # "health.log_meal"
    name: str                 # "Log Meal"
    description: str          # Used in LLM tool descriptions
    handler: Callable         # async def _log_meal(**kwargs): ...
    parameters_schema: dict   # JSON Schema for arguments
    domain: str = ""          # Auto-set by loader
```

### AgentDeclaration

```python
@dataclass
class AgentDeclaration:
    agent_type: str           # "health.nutrition_coach"
    name: str                 # "Nutrition Coach"
    description: str          # Short description
    system_prompt: str        # The agent's personality and instructions
    tools: list[str]          # Tool IDs this agent can call
    model_preference: str     # Override default LLM model (optional)
    temperature: float        # LLM temperature (default 0.7)
    max_tokens: int           # Max response tokens (default 2048)
```

### EventHandlerDeclaration

```python
@dataclass
class EventHandlerDeclaration:
    event_pattern: str        # "health.meal_logged" or "health.*"
    handler: Callable         # async def handler(event, session=None): ...
    description: str          # What this handler does
```

### MemoryCategoryDeclaration

```python
@dataclass
class MemoryCategoryDeclaration:
    category: str             # "dietary_preference"
    description: str          # "User's dietary preferences"
    example_keys: list[str]   # ["diet_type", "meal_preference"]
```

---

## What the Kernel Does at Startup

When the FastAPI app starts, `src/domains/loader.py` runs this sequence for each domain:

```
1. DISCOVER    Import src/domains/{domain}/__init__.py, find `plugin` attribute
2. VALIDATE    Call plugin.validate() — check naming, tool refs, structure
3. TOOLS       Register each ToolDeclaration into the shared ToolRegistry
4. AGENTS      Register each AgentDeclaration into the shared AgentRegistry
5. EVENTS      Subscribe each EventHandlerDeclaration to the EventBus
6. MEMORY      Store memory categories for the assembler
7. ROUTER      Mount plugin.get_router() at /api/v1/domains/{domain_id}
8. LIFECYCLE   Call plugin.on_startup() for custom initialisation
9. REPORT      Log: "domain_loaded domain=health tools=5 agents=2 events=2 memory=5 router=True"
```

After all domains are loaded:
```
"all_domains_loaded total=6 successful=6 failed=0"
```

Registries are stored on `app.state` for dependency injection in route handlers.

---

## Cross-Layer Validation

The arch test `test_domain_integration.py` performs these cross-layer checks:

| Check | What it catches |
|-------|----------------|
| Agent tools exist in get_tools() | Agent references `health.log_meal` but tool isn't declared |
| Tool handlers are async | Sync handler would block the event loop |
| Tool descriptions are > 10 chars | LLM needs meaningful descriptions for function-calling |
| Agent system prompts are > 20 chars | Empty prompts produce bad agent behaviour |
| Event patterns start with domain | Handler for `meal_logged` instead of `health.meal_logged` |
| Memory categories have example keys | Category without examples is unclear for the assembler |
| No tool ID collisions across domains | Two domains both declare `log_meal` |
| No agent type collisions across domains | Two domains both declare `advisor` |
| Manifest consistency | Plugin tools match manifest.py tools |

---

## Current Domains

| Domain | Tools | Agents | Events | Memory Categories |
|--------|-------|--------|--------|-------------------|
| **health** | 5 (log_meal, log_exercise, log_sleep, get_nutrition_summary, get_exercise_summary) | 2 (nutrition_coach, fitness_advisor) | 2 (meal_logged, vitals_recorded) | 5 |
| **finance** | 4 (log_transaction, get_spending_summary, get_budget_status, get_investment_summary) | 1 (budget_advisor) | 2 (transaction_logged, budget_updated) | 5 |
| **productivity** | 5 (create_task, complete_task, list_tasks, log_habit, get_daily_summary) | 2 (planner, focus_coach) | 2 (task_created, task_completed) | 5 |
| **relationships** | 4 (log_interaction, create_contact, get_contact, schedule_event) | 1 (social_advisor) | 2 (interaction_logged, reminder_due) | 4 |
| **learning** | 4 (add_resource, log_session, get_progress, capture_note) | 2 (tutor, study_planner) | 2 (resource_added, session_logged) | 5 |
| **home** | 4 (create_task, complete_task, add_to_shopping_list, get_maintenance_schedule) | 1 (household_manager) | 2 (task_created, maintenance_due) | 5 |

**Totals:** 26 tools, 9 agents, 12 event handlers, 29 memory categories across 6 domains.
