# Kernel Module (`src/kernel/`)

AI kernel: LLM client, prompt/tool registries, and the global orchestrator.

## Contents

| File | Purpose |
|------|---------|
| `llm_client.py` | `LLMClient` — LiteLLM-based provider-agnostic LLM calls (completion, structured output, tool calling) |
| `prompt_registry.py` | `PromptRegistry` — versioned prompt template management with YAML file loading |
| `tool_registry.py` | `ToolRegistry` — register, lookup, and invoke tools; OpenAI function-calling format export |
| `orchestrator.py` | `GlobalOrchestrator` — central brain: intent → memory → retrieval → tools → response → events |
| `prompts/` | YAML prompt template files |

## Orchestration Pipeline

1. **Intent classification** — determine domain, action, entities
2. **Memory assembly** — gather user context from all memory layers
3. **Retrieval** — hybrid RAG search for relevant knowledge
4. **Tool execution** — ReAct-style tool calling loop (up to 3 iterations)
5. **Response generation** — LLM completion with full context
6. **Event emission** — publish `system.message_processed` event
7. **Memory update** — append to short-term message history

## Tool Registration

```python
from src.kernel.tool_registry import tool_registry, ToolDefinition

tool_registry.register(
    ToolDefinition(tool_id="health.log_meal", name="Log Meal", description="...", domain="health", parameters_schema={...}),
    implementation=log_meal_handler,
)
```
