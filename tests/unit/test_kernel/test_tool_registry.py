"""
Unit tests for src/kernel/tool_registry.py — tool registration and invocation.

Tests:
  - test_register_and_get: Register a tool, retrieve definition
  - test_get_nonexistent: Missing tool returns None
  - test_list_tools: Lists all registered tools
  - test_list_tools_by_domain: Domain filtering works
  - test_invoke_sync_handler: Synchronous handler returns ToolResult with data
  - test_invoke_async_handler: Async handler returns ToolResult with data
  - test_invoke_not_found: Invoking unknown tool returns error ToolResult
  - test_invoke_handler_exception: Handler that raises returns error ToolResult
  - test_get_openai_tools_format: Export matches OpenAI function-calling schema
  - test_get_openai_tools_domain_filter: Domain filter applies to export
"""
import pytest

from src.kernel.tool_registry import ToolDefinition, ToolRegistry


class TestToolRegistry:
    """Verify tool registration, lookup, invocation, and export."""

    def setup_method(self):
        self.registry = ToolRegistry()

    def test_register_and_get(self):
        """Registered tool is retrievable."""
        defn = ToolDefinition(tool_id="test.tool", name="Test", description="A test")
        self.registry.register(defn, lambda: "ok")
        assert self.registry.get("test.tool") is not None

    def test_get_nonexistent(self):
        """Unknown tool_id returns None."""
        assert self.registry.get("nope") is None

    def test_list_tools(self):
        """list_tools() returns all definitions."""
        for i in range(3):
            self.registry.register(
                ToolDefinition(tool_id=f"t.{i}", name=f"T{i}", description=f"D{i}"),
                lambda: None,
            )
        assert len(self.registry.list_tools()) == 3

    def test_list_tools_by_domain(self):
        """Domain filter narrows results."""
        self.registry.register(
            ToolDefinition(tool_id="h.a", name="A", description="A", domain="health"),
            lambda: None,
        )
        self.registry.register(
            ToolDefinition(tool_id="f.a", name="B", description="B", domain="finance"),
            lambda: None,
        )
        assert len(self.registry.list_tools(domain="health")) == 1
        assert len(self.registry.list_tools(domain="finance")) == 1

    @pytest.mark.asyncio
    async def test_invoke_sync_handler(self):
        """Synchronous handler is wrapped and returns ToolResult."""
        self.registry.register(
            ToolDefinition(tool_id="sync.mul", name="Mul", description="Multiply"),
            lambda x: x * 2,
        )
        result = await self.registry.invoke("sync.mul", x=5)
        assert result.success is True
        assert result.data == 10

    @pytest.mark.asyncio
    async def test_invoke_async_handler(self):
        """Async handler is awaited and returns ToolResult."""
        async def add_one(x):
            return x + 1

        self.registry.register(
            ToolDefinition(tool_id="async.add", name="Add", description="Add one"),
            add_one,
        )
        result = await self.registry.invoke("async.add", x=10)
        assert result.success is True
        assert result.data == 11

    @pytest.mark.asyncio
    async def test_invoke_not_found(self):
        """Invoking unknown tool returns error result, not exception."""
        result = await self.registry.invoke("ghost.tool")
        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_invoke_handler_exception(self):
        """Handler that raises returns error ToolResult."""
        def bad_handler():
            raise ValueError("boom")

        self.registry.register(
            ToolDefinition(tool_id="bad.tool", name="Bad", description="Fails"),
            bad_handler,
        )
        result = await self.registry.invoke("bad.tool")
        assert result.success is False
        assert "boom" in result.error

    def test_get_openai_tools_format(self):
        """Export matches OpenAI function-calling schema."""
        self.registry.register(
            ToolDefinition(
                tool_id="test.fn", name="Test Fn", description="Does testing",
                parameters_schema={"type": "object", "properties": {"x": {"type": "integer"}}},
            ),
            lambda x: x,
        )
        tools = self.registry.get_openai_tools()
        assert len(tools) == 1
        assert tools[0]["type"] == "function"
        assert tools[0]["function"]["name"] == "test.fn"
        assert tools[0]["function"]["description"] == "Does testing"
        assert "properties" in tools[0]["function"]["parameters"]

    def test_get_openai_tools_domain_filter(self):
        """Domain filter applies to OpenAI export."""
        self.registry.register(
            ToolDefinition(tool_id="h.t", name="H", description="H", domain="health"),
            lambda: None,
        )
        self.registry.register(
            ToolDefinition(tool_id="f.t", name="F", description="F", domain="finance"),
            lambda: None,
        )
        health_tools = self.registry.get_openai_tools(domain="health")
        assert len(health_tools) == 1
        assert health_tools[0]["function"]["name"] == "h.t"
