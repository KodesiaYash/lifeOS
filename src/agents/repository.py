"""
Database access layer for agent entities.
"""
import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.models import AgentDefinition, AgentExecution


class AgentDefinitionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, definition: AgentDefinition) -> AgentDefinition:
        self.session.add(definition)
        await self.session.flush()
        return definition

    async def get_by_type(self, agent_type: str) -> AgentDefinition | None:
        result = await self.session.execute(
            select(AgentDefinition).where(
                AgentDefinition.agent_type == agent_type,
                AgentDefinition.active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def list_all(self, domain: str | None = None, active_only: bool = True) -> list[AgentDefinition]:
        stmt = select(AgentDefinition)
        if active_only:
            stmt = stmt.where(AgentDefinition.active.is_(True))
        if domain:
            stmt = stmt.where(AgentDefinition.domain == domain)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class AgentExecutionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, execution: AgentExecution) -> AgentExecution:
        self.session.add(execution)
        await self.session.flush()
        return execution

    async def get_by_id(self, execution_id: uuid.UUID) -> AgentExecution | None:
        return await self.session.get(AgentExecution, execution_id)

    async def update_status(
        self, execution_id: uuid.UUID, status: str, **kwargs: object
    ) -> None:
        values = {"status": status, **kwargs}
        await self.session.execute(
            update(AgentExecution)
            .where(AgentExecution.id == execution_id)
            .values(**values)
        )

    async def list_recent(
        self,
        agent_type: str | None = None,
        limit: int = 20,
    ) -> list[AgentExecution]:
        stmt = select(AgentExecution)
        if agent_type:
            stmt = stmt.where(AgentExecution.agent_type == agent_type)
        stmt = stmt.order_by(AgentExecution.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
