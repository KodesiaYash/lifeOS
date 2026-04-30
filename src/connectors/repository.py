"""
Database access layer for connector entities.
"""
import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.connectors.models import ConnectorDefinition, ConnectorInstance, SyncLog


class ConnectorDefinitionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, definition: ConnectorDefinition) -> ConnectorDefinition:
        self.session.add(definition)
        await self.session.flush()
        return definition

    async def get_by_type(self, connector_type: str) -> ConnectorDefinition | None:
        result = await self.session.execute(
            select(ConnectorDefinition).where(
                ConnectorDefinition.connector_type == connector_type,
                ConnectorDefinition.active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def list_all(self, active_only: bool = True) -> list[ConnectorDefinition]:
        stmt = select(ConnectorDefinition)
        if active_only:
            stmt = stmt.where(ConnectorDefinition.active.is_(True))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class ConnectorInstanceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, instance: ConnectorInstance) -> ConnectorInstance:
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get_by_id(self, instance_id: uuid.UUID) -> ConnectorInstance | None:
        return await self.session.get(ConnectorInstance, instance_id)

    async def list_by_user(
        self, tenant_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[ConnectorInstance]:
        result = await self.session.execute(
            select(ConnectorInstance).where(
                ConnectorInstance.tenant_id == tenant_id,
                ConnectorInstance.user_id == user_id,
                ConnectorInstance.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())

    async def update_status(
        self, instance_id: uuid.UUID, status: str, **kwargs: object
    ) -> None:
        values = {"status": status, **kwargs}
        await self.session.execute(
            update(ConnectorInstance)
            .where(ConnectorInstance.id == instance_id)
            .values(**values)
        )


class SyncLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, log: SyncLog) -> SyncLog:
        self.session.add(log)
        await self.session.flush()
        return log

    async def list_by_instance(
        self, instance_id: uuid.UUID, limit: int = 20
    ) -> list[SyncLog]:
        result = await self.session.execute(
            select(SyncLog)
            .where(SyncLog.instance_id == instance_id)
            .order_by(SyncLog.started_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
