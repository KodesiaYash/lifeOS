import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from src.agents.models import AgentDefinition, AgentExecution  # noqa: F401
from src.communication.models import ChannelAccount, ChannelIdentity, Conversation, Message  # noqa: F401
from src.config import settings
from src.connectors.models import ConnectorDefinition, ConnectorInstance, SyncLog  # noqa: F401

# Import all models so Alembic can discover them
from src.core.models import DomainRegistry, Settings  # noqa: F401
from src.events.models import Event  # noqa: F401
from src.knowledge.models import KnowledgeChunk, KnowledgeDocument, KnowledgeRelation  # noqa: F401
from src.memory.models import ConversationSummary, MemoryFact, SemanticMemory  # noqa: F401
from src.orchestration.models import WorkflowDefinition, WorkflowExecution, WorkflowStepExecution  # noqa: F401
from src.scheduling.models import BackgroundTask, ScheduledJob  # noqa: F401
from src.shared.base_model import Base

# Alembic Config object
config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Set up Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# SQLAlchemy MetaData for autogenerate support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
