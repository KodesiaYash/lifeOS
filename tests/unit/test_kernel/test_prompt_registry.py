"""
Unit tests for src/kernel/prompt_registry.py — versioned prompt template management.

Tests:
  - test_register_and_get: Register a template, retrieve by ID
  - test_get_nonexistent: Missing ID returns None
  - test_get_latest_version: Multiple versions → latest returned by default
  - test_get_specific_version: Can request a specific older version
  - test_render_substitution: Variables are substituted into template
  - test_render_missing_variable: Missing variable returns None (graceful failure)
  - test_render_nonexistent_prompt: Rendering unknown prompt returns None
  - test_list_all: Lists all registered prompt IDs
  - test_overwrite_same_version: Re-registering same version overwrites
"""
from src.kernel.prompt_registry import PromptRegistry, PromptTemplate


class TestPromptRegistry:
    """Verify prompt template registration, versioning, and rendering."""

    def setup_method(self):
        self.registry = PromptRegistry()

    def test_register_and_get(self):
        """Registered template is retrievable by ID."""
        tpl = PromptTemplate(
            prompt_id="test.greeting",
            version=1,
            template="Hello {name}, welcome to {app}!",
            input_variables=["name", "app"],
        )
        self.registry.register(tpl)
        result = self.registry.get("test.greeting")
        assert result is not None
        assert result.prompt_id == "test.greeting"

    def test_get_nonexistent(self):
        """Unknown prompt ID returns None."""
        assert self.registry.get("nonexistent") is None

    def test_get_latest_version(self):
        """When multiple versions exist, get() returns the latest."""
        for v in [1, 2, 3]:
            self.registry.register(PromptTemplate(
                prompt_id="test.versioned", version=v, template=f"V{v}",
            ))
        result = self.registry.get("test.versioned")
        assert result.version == 3

    def test_get_specific_version(self):
        """Can request a specific older version by number."""
        for v in [1, 2]:
            self.registry.register(PromptTemplate(
                prompt_id="test.specific", version=v, template=f"V{v}",
            ))
        result = self.registry.get("test.specific", version=1)
        assert result.version == 1
        assert "V1" in result.template

    def test_render_substitution(self):
        """Variables in {braces} are replaced with provided values."""
        self.registry.register(PromptTemplate(
            prompt_id="test.render", template="Hello {name}!", input_variables=["name"],
        ))
        assert self.registry.render("test.render", name="Alice") == "Hello Alice!"

    def test_render_missing_variable(self):
        """Missing variable causes render to return None (not crash)."""
        self.registry.register(PromptTemplate(
            prompt_id="test.missing", template="Hello {name}!",
        ))
        result = self.registry.render("test.missing")
        assert result is None

    def test_render_nonexistent_prompt(self):
        """Rendering an unknown prompt ID returns None."""
        result = self.registry.render("does.not.exist", name="Bob")
        assert result is None

    def test_list_all(self):
        """list_all() returns all registered prompt IDs."""
        self.registry.register(PromptTemplate(prompt_id="a", template="A"))
        self.registry.register(PromptTemplate(prompt_id="b", template="B"))
        assert sorted(self.registry.list_all()) == ["a", "b"]

    def test_overwrite_same_version(self):
        """Re-registering same ID + version overwrites the template."""
        self.registry.register(PromptTemplate(
            prompt_id="test.ow", version=1, template="Old",
        ))
        self.registry.register(PromptTemplate(
            prompt_id="test.ow", version=1, template="New",
        ))
        result = self.registry.get("test.ow")
        assert "New" in result.template
