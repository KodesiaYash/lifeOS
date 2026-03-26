"""
Pydantic schemas for core entities: request/response models.

Single-user mode: Only Settings and DomainRegistry schemas.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# --- Settings ---

class SettingsRead(BaseModel):
    id: uuid.UUID
    timezone: str
    language: str
    preferences: dict
    active_domains: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SettingsUpdate(BaseModel):
    timezone: str | None = None
    language: str | None = None
    preferences: dict | None = None
    active_domains: list[str] | None = None


# --- DomainRegistry ---

class DomainRegistryRead(BaseModel):
    id: uuid.UUID
    domain_id: str
    name: str
    version: str
    description: str | None
    manifest: dict
    active: bool
    config: dict
    installed_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DomainRegistryUpdate(BaseModel):
    active: bool | None = None
    config: dict | None = None
