"""
Integration test conftest — real database sessions for cross-module flows.

Integration tests:
  - Use real SQLite (in-memory) for SQL operations
  - Mock Redis and LLM calls
  - Test module-to-module data flows through real DB
"""
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import test_session_factory


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    """Alias for db_session — used in integration tests for clarity."""
    async with test_session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def mock_redis() -> AsyncMock:
    """
    Mock Redis client for short-term memory tests.
    Simulates get/set/expire with an in-memory dict.
    """
    store = {}

    client = AsyncMock()

    async def _set(key, value, ex=None):
        store[key] = value

    async def _get(key):
        return store.get(key)

    async def _delete(key):
        store.pop(key, None)

    async def _exists(key):
        return key in store

    client.set = AsyncMock(side_effect=_set)
    client.get = AsyncMock(side_effect=_get)
    client.delete = AsyncMock(side_effect=_delete)
    client.exists = AsyncMock(side_effect=_exists)
    client._store = store  # exposed for assertions

    return client


@pytest.fixture
def mock_embedding_service() -> AsyncMock:
    """
    Mock embedding service that returns deterministic vectors.
    Returns a 4-dimensional vector for testing (not 1536).
    """
    service = AsyncMock()

    async def _embed(texts):
        return [[0.1 * i, 0.2 * i, 0.3 * i, 0.4 * i] for i, _ in enumerate(texts, 1)]

    service.embed_batch = AsyncMock(side_effect=_embed)
    service.embed = AsyncMock(return_value=[0.1, 0.2, 0.3, 0.4])
    return service
