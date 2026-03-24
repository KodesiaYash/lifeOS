"""
Tests for the kernel module.
"""
import pytest

from src.kernel.prompt_registry import PromptRegistry, PromptTemplate
from src.kernel.tool_registry import ToolDefinition, ToolRegistry, ToolResult


class TestPromptRegistry:
    def setup_method(self):
        self.registry = PromptRegistry()

    def test_register_and_get(self):
        template = PromptTemplate(
            prompt_id="test.greeting",
            version=1,
            template="Hello {name}, welcome to {app}!",
            input_variables=["name", "app"],
        )
        self.registry.register(template)
        result = self.registry.get("test.greeting")
        assert result is not None
        assert result.prompt_id == "test.greeting"

    def test_get_nonexistent(self):
        assert self.registry.get("nonexistent") is None

    def test_get_latest_version(self):
        for v in [1, 2, 3]:
            self.registry.register(PromptTemplate(
                prompt_id="test.versioned",
                version=v,
                template=f"Version {v}",
            ))
        result = self.registry.get("test.versioned")
        assert result is not None
        assert result.version == 3

    def test_get_specific_version(self):
        for v in [1, 2]:
            self.registry.register(PromptTemplate(
                prompt_id="test.specific",
                version=v,
                template=f"Version {v}",
            ))
        result = self.registry.get("test.specific", version=1)
        assert result is not None
        assert result.version == 1

    def test_render(self):
        self.registry.register(PromptTemplate(
            prompt_id="test.render",
            template="Hello {name}!",
            input_variables=["name"],
        ))
        rendered = self.registry.render("test.render", name="Alice")
        assert rendered == "Hello Alice!"

    def test_render_missing_variable(self):
        self.registry.register(PromptTemplate(
            prompt_id="test.missing",
            template="Hello {name}!",
        ))
        result = self.registry.render("test.missing")
        assert result is None  # Render error returns None

    def test_list_all(self):
        self.registry.register(PromptTemplate(prompt_id="a", template="A"))
        self.registry.register(PromptTemplate(prompt_id="b", template="B"))
        assert sorted(self.registry.list_all()) == ["a", "b"]


class TestToolRegistry:
    def setup_method(self):
        self.registry = ToolRegistry()

    def test_register_and_get(self):
        definition = ToolDefinition(
            tool_id="test.tool",
            name="Test Tool",
            description="A test tool",
        )
        self.registry.register(definition, lambda: "result")
        assert self.registry.get("test.tool") is not None

    def test_get_nonexistent(self):
        assert self.registry.get("nonexistent") is None

    def test_list_tools(self):
        for i in range(3):
            self.registry.register(
                ToolDefinition(tool_id=f"tool.{i}", name=f"Tool {i}", description=f"Desc {i}"),
                lambda: None,
            )
        assert len(self.registry.list_tools()) == 3

    def test_list_tools_by_domain(self):
        self.registry.register(
            ToolDefinition(tool_id="health.a", name="A", description="A", domain="health"),
            lambda: None,
        )
        self.registry.register(
            ToolDefinition(tool_id="finance.a", name="B", description="B", domain="finance"),
            lambda: None,
        )
        assert len(self.registry.list_tools(domain="health")) == 1

    @pytest.mark.asyncio
    async def test_invoke_sync(self):
        self.registry.register(
            ToolDefinition(tool_id="sync.tool", name="Sync", description="Sync tool"),
            lambda x: x * 2,
        )
        result = await self.registry.invoke("sync.tool", x=5)
        assert result.success is True
        assert result.data == 10

    @pytest.mark.asyncio
    async def test_invoke_async(self):
        async def async_handler(x):
            return x + 1

        self.registry.register(
            ToolDefinition(tool_id="async.tool", name="Async", description="Async tool"),
            async_handler,
        )
        result = await self.registry.invoke("async.tool", x=10)
        assert result.success is True
        assert result.data == 11

    @pytest.mark.asyncio
    async def test_invoke_not_found(self):
        result = await self.registry.invoke("nonexistent")
        assert result.success is False
        assert "not found" in result.error.lower()

    def test_get_openai_tools(self):
        self.registry.register(
            ToolDefinition(
                tool_id="test.fn",
                name="Test Function",
                description="Does testing",
                parameters_schema={"type": "object", "properties": {"x": {"type": "integer"}}},
            ),
            lambda x: x,
        )
        tools = self.registry.get_openai_tools()
        assert len(tools) == 1
        assert tools[0]["type"] == "function"
        assert tools[0]["function"]["name"] == "test.fn"
