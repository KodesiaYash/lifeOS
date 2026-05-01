"""
Seed script: populate the database with the current platform scaffolding.

Usage:
    python -m scripts.seed
"""

from __future__ import annotations

import asyncio

from src.communication.bootstrap import CommunicationBootstrap
from src.core.models import DomainRegistry
from src.core.repository import DomainRegistryRepository, SettingsRepository
from src.domains.loader import discover_domain_plugins
from src.shared.database import async_session_factory


async def seed_data() -> None:
    """Seed singleton settings, domain registry entries, and default channels."""
    async with async_session_factory() as session:
        settings_repo = SettingsRepository(session)
        domain_repo = DomainRegistryRepository(session)

        settings = await settings_repo.get_or_create()
        settings.timezone = settings.timezone or "UTC"
        settings.language = settings.language or "en"
        settings.preferences = settings.preferences or {
            "theme": "system",
            "notifications_enabled": True,
        }

        plugins = discover_domain_plugins()
        active_domains: list[str] = []
        for plugin in plugins:
            active_domains.append(plugin.domain_id)
            payload = {
                "name": plugin.name,
                "version": plugin.version,
                "description": plugin.description,
                "manifest": plugin.get_manifest(),
                "active": True,
            }
            existing = await domain_repo.get_by_domain_id(plugin.domain_id)
            if existing is None:
                await domain_repo.register(
                    DomainRegistry(
                        domain_id=plugin.domain_id,
                        **payload,
                    )
                )
            else:
                await domain_repo.update(plugin.domain_id, **payload)

        settings.active_domains = sorted(active_domains)

        bootstrap = CommunicationBootstrap(session)
        channel_bindings = await bootstrap.ensure_default_accounts()

        await session.commit()
        print("Seed data created successfully.")
        print(f"  Settings row ready: timezone={settings.timezone} language={settings.language}")
        print(f"  Domains registered: {len(active_domains)}")
        print(f"  Channel accounts ready: {len(channel_bindings)}")


if __name__ == "__main__":
    asyncio.run(seed_data())
