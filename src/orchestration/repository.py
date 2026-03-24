"""
Database access layer for workflow orchestration.
"""
import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.orchestration.models import WorkflowDefinition, WorkflowExecution, WorkflowStepExecution


class WorkflowDefinitionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, definition: WorkflowDefinition) -> WorkflowDefinition:
        self.session.add(definition)
        await self.session.flush()
        return definition

    async def get_by_id(self, definition_id: uuid.UUID) -> WorkflowDefinition | None:
        return await self.session.get(WorkflowDefinition, definition_id)

    async def list_by_tenant(
        self, tenant_id: uuid.UUID, domain: str | None = None, active_only: bool = True
    ) -> list[WorkflowDefinition]:
        stmt = select(WorkflowDefinition).where(WorkflowDefinition.tenant_id == tenant_id)
        if domain:
            stmt = stmt.where(WorkflowDefinition.domain == domain)
        if active_only:
            stmt = stmt.where(WorkflowDefinition.active == True)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_trigger(
        self, tenant_id: uuid.UUID, trigger_type: str
    ) -> list[WorkflowDefinition]:
        result = await self.session.execute(
            select(WorkflowDefinition).where(
                WorkflowDefinition.tenant_id == tenant_id,
                WorkflowDefinition.trigger_type == trigger_type,
                WorkflowDefinition.active == True,
            )
        )
        return list(result.scalars().all())


class WorkflowExecutionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, execution: WorkflowExecution) -> WorkflowExecution:
        self.session.add(execution)
        await self.session.flush()
        return execution

    async def get_by_id(self, execution_id: uuid.UUID) -> WorkflowExecution | None:
        return await self.session.get(WorkflowExecution, execution_id)

    async def update_status(
        self, execution_id: uuid.UUID, status: str, **kwargs: object
    ) -> None:
        values = {"status": status, **kwargs}
        await self.session.execute(
            update(WorkflowExecution)
            .where(WorkflowExecution.id == execution_id)
            .values(**values)
        )

    async def list_active(self, tenant_id: uuid.UUID) -> list[WorkflowExecution]:
        result = await self.session.execute(
            select(WorkflowExecution).where(
                WorkflowExecution.tenant_id == tenant_id,
                WorkflowExecution.status.in_(["pending", "running", "paused"]),
            )
        )
        return list(result.scalars().all())


class WorkflowStepExecutionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, step: WorkflowStepExecution) -> WorkflowStepExecution:
        self.session.add(step)
        await self.session.flush()
        return step

    async def list_by_execution(self, execution_id: uuid.UUID) -> list[WorkflowStepExecution]:
        result = await self.session.execute(
            select(WorkflowStepExecution)
            .where(WorkflowStepExecution.execution_id == execution_id)
            .order_by(WorkflowStepExecution.step_index)
        )
        return list(result.scalars().all())
