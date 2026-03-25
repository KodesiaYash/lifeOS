"""
Root conftest — shared fixtures available to ALL test tiers.

Test tiers:
    tests/unit/         — isolated logic tests, mocks only, no I/O
    tests/integration/  — real DB/Redis, cross-module flows
    tests/e2e/          — full HTTP pipeline with cassettes
    tests/drift/        — nightly real-LLM behavioural tests
    tests/arch/         — architecture & requirement coverage tests
"""
import asyncio
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.shared.base_model import Base

# ---------------------------------------------------------------------------
# Database (SQLite in-memory for unit tests; overridden in integration/)
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_factory = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean database session per test."""
    async with test_session_factory() as session:
        yield session
        await session.rollback()


# ---------------------------------------------------------------------------
# Identity fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.UUID("00000000-0000-0000-0000-000000000002")


@pytest.fixture
def correlation_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def now() -> datetime:
    return datetime.now(timezone.utc)
