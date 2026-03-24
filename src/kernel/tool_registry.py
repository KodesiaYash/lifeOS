"""
Tool registration, lookup, and invocation.
Tools are deterministic functions that agents can call.
"""
import inspect
from collections.abc import Callable
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger()


class ToolDefinition(BaseModel):
    """Metadata for a registered tool."""
    tool_id: str
    name: str
    description: str
    domain: str | None = None
    parameters_schema: dict = Field(default_factory=dict)  # JSON Schema for parameters
    requires_confirmation: bool = False
    is_deterministic: bool = True


class ToolResult(BaseModel):
    """Result from a tool invocation."""
    tool_id: str
    success: bool
    data: Any = None
    error: str | None = None


class ToolRegistry:
    """
    Registry for tools that agents can invoke.
    Tools are registered with metadata and a callable implementation.
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        self._implementations: dict[str, Callable] = {}

    def register(
        self,
        definition: ToolDefinition,
        implementation: Callable,
    ) -> None:
        """Register a tool with its definition and implementation."""
        self._tools[definition.tool_id] = definition
        self._implementations[definition.tool_id] = implementation
        logger.debug("tool_registered", tool_id=definition.tool_id, domain=definition.domain)

    def get(self, tool_id: str) -> ToolDefinition | None:
        """Get a tool definition by ID."""
        return self._tools.get(tool_id)

    def list_tools(self, domain: str | None = None) -> list[ToolDefinition]:
        """List all registered tools, optionally filtered by domain."""
        tools = list(self._tools.values())
        if domain is not None:
            tools = [t for t in tools if t.domain == domain]
        return tools

    def get_openai_tools(self, domain: str | None = None) -> list[dict]:
        """
        Get tool definitions in OpenAI function-calling format.
        Suitable for passing to LLM tool calls.
        """
        tools = self.list_tools(domain)
        return [
            {
                "type": "function",
                "function": {
                    "name": t.tool_id,
                    "description": t.description,
                    "parameters": t.parameters_schema,
                },
            }
            for t in tools
        ]

    async def invoke(self, tool_id: str, **kwargs: Any) -> ToolResult:
        """Invoke a registered tool by ID."""
        if tool_id not in self._implementations:
            return ToolResult(tool_id=tool_id, success=False, error=f"Tool not found: {tool_id}")

        impl = self._implementations[tool_id]
        try:
            if inspect.iscoroutinefunction(impl):
                result = await impl(**kwargs)
            else:
                result = impl(**kwargs)
            logger.info("tool_invoked", tool_id=tool_id, success=True)
            return ToolResult(tool_id=tool_id, success=True, data=result)
        except Exception as e:
            logger.exception("tool_invocation_error", tool_id=tool_id)
            return ToolResult(tool_id=tool_id, success=False, error=str(e))


# Singleton registry
tool_registry = ToolRegistry()
