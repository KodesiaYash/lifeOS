"""
Prompt template registry with versioning.
Loads prompt templates from YAML files and provides them by ID and version.
"""
from pathlib import Path
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger()

PROMPTS_DIR = Path(__file__).parent / "prompts"


class PromptTemplate(BaseModel):
    """A versioned prompt template."""
    prompt_id: str
    version: int = 1
    template: str
    input_variables: list[str] = Field(default_factory=list)
    model_preference: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None
    description: str | None = None


class PromptRegistry:
    """
    File-based prompt template registry.
    Templates are loaded from YAML files in src/kernel/prompts/.
    Supports versioning and runtime registration.
    """

    def __init__(self) -> None:
        self._templates: dict[str, dict[int, PromptTemplate]] = {}

    def register(self, template: PromptTemplate) -> None:
        """Register a prompt template."""
        if template.prompt_id not in self._templates:
            self._templates[template.prompt_id] = {}
        self._templates[template.prompt_id][template.version] = template
        logger.debug(
            "prompt_registered",
            prompt_id=template.prompt_id,
            version=template.version,
        )

    def get(self, prompt_id: str, version: int | None = None) -> PromptTemplate | None:
        """
        Get a prompt template by ID and optional version.
        If version is None, returns the latest version.
        """
        versions = self._templates.get(prompt_id)
        if not versions:
            return None
        if version is not None:
            return versions.get(version)
        # Return latest version
        latest = max(versions.keys())
        return versions[latest]

    def render(
        self, prompt_id: str, version: int | None = None, **variables: Any
    ) -> str | None:
        """
        Get a prompt template and render it with the given variables.
        Uses Python str.format() for simple variable substitution.
        """
        template = self.get(prompt_id, version)
        if template is None:
            logger.warning("prompt_not_found", prompt_id=prompt_id, version=version)
            return None
        try:
            return template.template.format(**variables)
        except KeyError as e:
            logger.error("prompt_render_error", prompt_id=prompt_id, missing_var=str(e))
            return None

    def list_all(self) -> list[str]:
        """List all registered prompt IDs."""
        return list(self._templates.keys())

    def load_from_directory(self, directory: Path | None = None) -> int:
        """
        Load prompt templates from YAML files in the given directory.
        Returns the number of templates loaded.
        """
        directory = directory or PROMPTS_DIR
        if not directory.exists():
            logger.warning("prompts_directory_not_found", path=str(directory))
            return 0

        count = 0
        for filepath in directory.glob("*.yaml"):
            try:
                import yaml
                with open(filepath) as f:
                    data = yaml.safe_load(f)
                if data:
                    template = PromptTemplate(**data)
                    self.register(template)
                    count += 1
            except Exception:
                logger.exception("prompt_load_error", file=str(filepath))
        logger.info("prompts_loaded", count=count, directory=str(directory))
        return count


# Singleton registry
prompt_registry = PromptRegistry()
