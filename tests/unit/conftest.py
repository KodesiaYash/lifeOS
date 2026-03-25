"""
Unit test conftest — provides mocks for external dependencies.

Unit tests must:
  - Never hit a real database, Redis, or LLM API
  - Use mocks/fakes for all I/O boundaries
  - Run in < 1 second total
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.events.bus import EventBus
from src.kernel.prompt_registry import PromptRegistry
from src.kernel.tool_registry import ToolRegistry


@pytest.fixture
def mock_event_bus() -> EventBus:
    """Fresh in-memory event bus for isolated tests."""
    return EventBus()


@pytest.fixture
def mock_prompt_registry() -> PromptRegistry:
    """Fresh prompt registry (no YAML loading)."""
    return PromptRegistry()


@pytest.fixture
def mock_tool_registry() -> ToolRegistry:
    """Fresh tool registry (no pre-registered tools)."""
    return ToolRegistry()


@pytest.fixture
def mock_llm_client() -> MagicMock:
    """
    Mock LLMClient that returns canned responses.
    Override return values in individual tests as needed.
    """
    client = AsyncMock()
    client.complete = AsyncMock(return_value="Mocked LLM response")
    client.structured_output = AsyncMock(return_value={"intent": "test", "confidence": 0.9})
    client.complete_with_tools = AsyncMock(return_value={
        "content": "Mocked tool response",
        "tool_calls": [],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50},
    })
    return client


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Mock async database session."""
    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session
