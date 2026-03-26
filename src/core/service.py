"""
Business logic for core entities.

Single-user mode: Settings and domain management only.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import DomainRegistry, Settings
from src.core.repository import DomainRegistryRepository, SettingsRepository
from src.core.schemas import DomainRegistryUpdate, SettingsUpdate


class CoreService:
    """Service layer for core platform operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings_repo = SettingsRepository(session)
        self.domains_repo = DomainRegistryRepository(session)

    async def get_settings(self) -> Settings:
        """Get application settings."""
        return await self.settings_repo.get_or_create()

    async def update_settings(self, data: SettingsUpdate) -> Settings:
        """Update application settings."""
        return await self.settings_repo.update(
            timezone=data.timezone,
            language=data.language,
            preferences=data.preferences,
            active_domains=data.active_domains,
        )

    async def list_domains(self) -> list[DomainRegistry]:
        """List all registered domains."""
        return await self.domains_repo.list_all()

    async def get_domain(self, domain_id: str) -> DomainRegistry | None:
        """Get a domain by ID."""
        return await self.domains_repo.get_by_domain_id(domain_id)

    async def update_domain(self, domain_id: str, data: DomainRegistryUpdate) -> DomainRegistry | None:
        """Update domain configuration."""
        return await self.domains_repo.update(
            domain_id,
            active=data.active,
            config=data.config,
        )
