# Agents Module (`src/agents/`)

Generic agent system with ReAct-style tool calling runtime.

## Contents

| File | Purpose |
|------|---------|
| `models.py` | SQLAlchemy models: AgentDefinition (global), AgentExecution (session-scoped) |
| `schemas.py` | Pydantic schemas: create/read/invoke request/response |
| `repository.py` | Database access for agent definitions and executions |
| `runtime.py` | `AgentRuntime` — ReAct loop: LLM call → tool calls → repeat → response |
| `registry.py` | `AgentRegistry` — in-memory agent lookup for fast routing |

## Agent Execution Flow

1. Load agent definition (system prompt, tools, model preferences)
2. Build messages with context
3. ReAct loop (max 5 iterations):
   - LLM call with tools
   - Execute tool calls
   - Append tool results to messages
   - Repeat until LLM returns text response
4. Persist execution record (tokens, duration, tool calls)

## Defining Agents

Agents are defined in the `agent_definitions` table with:
- `agent_type` — unique identifier (e.g., `health.nutrition_coach`)
- `system_prompt` — the agent's personality and instructions
- `tools` — list of tool IDs the agent can use
- `domain` — optional domain affiliation
- `model_preference` — preferred LLM model
