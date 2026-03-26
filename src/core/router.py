"""
API endpoints for core entities (settings, domains).

Single-user mode: No tenant/user management needed.
"""

from fastapi import APIRouter, HTTPException

from src.core.schemas import (
    DomainRegistryRead,
    DomainRegistryUpdate,
    SettingsRead,
    SettingsUpdate,
)
from src.core.service import CoreService
from src.dependencies import DbSession

router = APIRouter()


@router.get("/settings", response_model=SettingsRead)
async def get_settings(db: DbSession) -> SettingsRead:
    """Get application settings."""
    service = CoreService(db)
    settings = await service.get_settings()
    return SettingsRead.model_validate(settings)


@router.patch("/settings", response_model=SettingsRead)
async def update_settings(data: SettingsUpdate, db: DbSession) -> SettingsRead:
    """Update application settings."""
    service = CoreService(db)
    settings = await service.update_settings(data)
    return SettingsRead.model_validate(settings)


@router.get("/domains", response_model=list[DomainRegistryRead])
async def list_domains(db: DbSession) -> list[DomainRegistryRead]:
    """List all registered domains."""
    service = CoreService(db)
    domains = await service.list_domains()
    return [DomainRegistryRead.model_validate(d) for d in domains]


@router.get("/domains/{domain_id}", response_model=DomainRegistryRead)
async def get_domain(domain_id: str, db: DbSession) -> DomainRegistryRead:
    """Get a specific domain by ID."""
    service = CoreService(db)
    domain = await service.get_domain(domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return DomainRegistryRead.model_validate(domain)


@router.patch("/domains/{domain_id}", response_model=DomainRegistryRead)
async def update_domain(
    domain_id: str,
    data: DomainRegistryUpdate,
    db: DbSession,
) -> DomainRegistryRead:
    """Update domain configuration."""
    service = CoreService(db)
    domain = await service.update_domain(domain_id, data)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return DomainRegistryRead.model_validate(domain)
