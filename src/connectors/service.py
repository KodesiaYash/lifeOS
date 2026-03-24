"""
Connector management service: install, sync, and manage external connectors.
"""
import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.connectors.models import ConnectorInstance, SyncLog
from src.connectors.repository import ConnectorDefinitionRepository, ConnectorInstanceRepository, SyncLogRepository
from src.connectors.schemas import ConnectorInstanceCreate
from src.shared.crypto import encrypt
from src.shared.time import utc_now

logger = structlog.get_logger()


class ConnectorService:
    """Manages connector lifecycle: install, configure, sync, disconnect."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.definitions = ConnectorDefinitionRepository(session)
        self.instances = ConnectorInstanceRepository(session)
        self.sync_logs = SyncLogRepository(session)

    async def install_connector(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        data: ConnectorInstanceCreate,
    ) -> ConnectorInstance:
        """Install a new connector instance for a user."""
        # Verify connector type exists
        definition = await self.definitions.get_by_type(data.connector_type)
        if definition is None:
            raise ValueError(f"Unknown connector type: {data.connector_type}")

        # Encrypt credentials
        import json
        credentials_encrypted = None
        if data.credentials:
            credentials_encrypted = encrypt(json.dumps(data.credentials))

        instance = ConnectorInstance(
            tenant_id=tenant_id,
            user_id=user_id,
            connector_type=data.connector_type,
            display_name=data.display_name,
            credentials_encrypted=credentials_encrypted,
            config=data.config,
            sync_frequency_minutes=data.sync_frequency_minutes,
            status="active",
        )
        instance = await self.instances.create(instance)

        logger.info(
            "connector_installed",
            instance_id=str(instance.id),
            connector_type=data.connector_type,
        )
        return instance

    async def trigger_sync(
        self,
        instance_id: uuid.UUID,
        full: bool = False,
    ) -> SyncLog:
        """Trigger a sync operation for a connector instance."""
        instance = await self.instances.get_by_id(instance_id)
        if instance is None:
            raise ValueError(f"Connector instance not found: {instance_id}")

        sync_log = SyncLog(
            tenant_id=instance.tenant_id,
            instance_id=instance_id,
            sync_type="full" if full else "incremental",
            status="running",
            started_at=utc_now(),
        )
        sync_log = await self.sync_logs.create(sync_log)

        # TODO: Dispatch actual sync to background worker
        logger.info(
            "connector_sync_triggered",
            instance_id=str(instance_id),
            sync_type=sync_log.sync_type,
        )
        return sync_log
