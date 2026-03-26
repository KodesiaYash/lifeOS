"""
Database access layer for scheduling entities.

Single-user mode: No tenant_id or user_id filtering.
"""

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.scheduling.models import BackgroundTask, ScheduledJob


class ScheduledJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, job: ScheduledJob) -> ScheduledJob:
        self.session.add(job)
        await self.session.flush()
        return job

    async def get_by_id(self, job_id: uuid.UUID) -> ScheduledJob | None:
        return await self.session.get(ScheduledJob, job_id)

    async def list_active(self) -> list[ScheduledJob]:
        stmt = select(ScheduledJob).where(ScheduledJob.active.is_(True))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def deactivate(self, job_id: uuid.UUID) -> None:
        await self.session.execute(update(ScheduledJob).where(ScheduledJob.id == job_id).values(active=False))

    async def record_run(self, job_id: uuid.UUID, success: bool, next_run_at=None) -> None:
        values: dict = {"run_count": ScheduledJob.run_count + 1}
        if not success:
            values["error_count"] = ScheduledJob.error_count + 1
        if next_run_at:
            values["next_run_at"] = next_run_at
        from src.shared.time import utc_now

        values["last_run_at"] = utc_now()
        await self.session.execute(update(ScheduledJob).where(ScheduledJob.id == job_id).values(**values))


class BackgroundTaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, task: BackgroundTask) -> BackgroundTask:
        self.session.add(task)
        await self.session.flush()
        return task

    async def get_by_id(self, task_id: uuid.UUID) -> BackgroundTask | None:
        return await self.session.get(BackgroundTask, task_id)

    async def update_status(self, task_id: uuid.UUID, status: str, **kwargs: object) -> None:
        values = {"status": status, **kwargs}
        await self.session.execute(update(BackgroundTask).where(BackgroundTask.id == task_id).values(**values))

    async def list_pending(self, limit: int = 20) -> list[BackgroundTask]:
        result = await self.session.execute(
            select(BackgroundTask)
            .where(BackgroundTask.status.in_(["pending", "retrying"]))
            .order_by(BackgroundTask.priority.asc(), BackgroundTask.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
