"""
arq worker for async background task processing.

Single-user mode: No tenant_id or user_id needed.
"""

import structlog
from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from src.config import settings

logger = structlog.get_logger()

_pool: ArqRedis | None = None


async def get_arq_pool() -> ArqRedis:
    """Get or create the arq Redis connection pool."""
    global _pool
    if _pool is None:
        _pool = await create_pool(
            RedisSettings.from_dsn(settings.REDIS_URL),
        )
    return _pool


async def enqueue_task(
    task_type: str,
    **kwargs,
) -> str | None:
    """Enqueue a background task via arq."""
    pool = await get_arq_pool()
    job = await pool.enqueue_job(task_type, **kwargs)
    if job is None:
        logger.warning("task_enqueue_failed", task_type=task_type)
        return None
    logger.info("task_enqueued", task_type=task_type, job_id=job.job_id)
    return job.job_id


# --- Task Handlers ---
# These are the actual handler functions that arq workers call.
# New handlers should be registered here and in WorkerSettings.functions.


async def process_knowledge_ingestion(ctx: dict, document_id: str) -> dict:
    """Background task: process a knowledge document through the ingestion pipeline."""
    logger.info("bg_knowledge_ingestion", document_id=document_id)
    # TODO: Wire up to IngestionPipeline
    return {"status": "completed", "document_id": document_id}


async def process_memory_consolidation(ctx: dict, session_id: str | None = None) -> dict:
    """Background task: consolidate short-term memory into long-term storage."""
    logger.info("bg_memory_consolidation", session_id=session_id)
    # TODO: Wire up to MemoryConsolidator
    return {"status": "completed"}


async def process_connector_sync(ctx: dict, connector_id: str) -> dict:
    """Background task: sync data from an external connector."""
    logger.info("bg_connector_sync", connector_id=connector_id)
    # TODO: Wire up to connector sync logic
    return {"status": "completed", "connector_id": connector_id}


class WorkerSettings:
    """arq worker configuration."""

    functions = [
        process_knowledge_ingestion,
        process_memory_consolidation,
        process_connector_sync,
    ]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 10
    job_timeout = 600  # 10 minutes
    retry_jobs = True
    max_tries = 3
