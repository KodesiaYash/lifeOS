"""
Database access layer for core entities.

Single-user mode: Only Settings and DomainRegistry repositories.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import DomainRegistry, Settings


class SettingsRepository:
    """Repository for application settings (singleton pattern)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create(self) -> Settings:
        """Get the settings row, creating it if it doesn't exist."""
        result = await self.session.execute(select(Settings).limit(1))
        settings = result.scalar_one_or_none()
        if settings is None:
            settings = Settings()
            self.session.add(settings)
            await self.session.flush()
        return settings

    async def update(self, **kwargs: object) -> Settings:
        """Update settings with the given values."""
        settings = await self.get_or_create()
        for key, value in kwargs.items():
            if value is not None and hasattr(settings, key):
                setattr(settings, key, value)
        await self.session.flush()
        return settings


class DomainRegistryRepository:
    """Repository for domain plugin registry."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def register(self, domain: DomainRegistry) -> DomainRegistry:
        self.session.add(domain)
        await self.session.flush()
        return domain

    async def get_by_domain_id(self, domain_id: str) -> DomainRegistry | None:
        result = await self.session.execute(
            select(DomainRegistry).where(DomainRegistry.domain_id == domain_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[DomainRegistry]:
        result = await self.session.execute(select(DomainRegistry))
        return list(result.scalars().all())

    async def list_active(self) -> list[DomainRegistry]:
        result = await self.session.execute(
            select(DomainRegistry).where(DomainRegistry.active.is_(True))
        )
        return list(result.scalars().all())

    async def update(self, domain_id: str, **kwargs: object) -> DomainRegistry | None:
        domain = await self.get_by_domain_id(domain_id)
        if domain is None:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(domain, key):
                setattr(domain, key, value)
        await self.session.flush()
        return domain
