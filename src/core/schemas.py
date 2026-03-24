"""
Pydantic schemas for core entities: request/response models.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# --- Tenant ---

class TenantCreate(BaseModel):
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=63, pattern=r"^[a-z0-9\-]+$")
    plan: str = Field(default="personal", max_length=50)
    settings: dict = Field(default_factory=dict)


class TenantRead(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    plan: str
    settings: dict
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TenantUpdate(BaseModel):
    name: str | None = None
    plan: str | None = None
    settings: dict | None = None


# --- User ---

class UserCreate(BaseModel):
    email: str | None = Field(default=None, max_length=255)
    name: str | None = Field(default=None, max_length=255)
    display_name: str | None = Field(default=None, max_length=100)
    timezone: str = Field(default="UTC", max_length=50)
    language: str = Field(default="en", max_length=10)


class UserRead(BaseModel):
    id: uuid.UUID
    email: str | None
    name: str | None
    display_name: str | None
    timezone: str
    language: str
    active: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    name: str | None = None
    display_name: str | None = None
    timezone: str | None = None
    language: str | None = None


# --- TenantUser ---

class TenantUserCreate(BaseModel):
    user_id: uuid.UUID
    role: str = Field(default="member", max_length=20)


class TenantUserRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    active: bool
    joined_at: datetime

    model_config = {"from_attributes": True}


# --- Workspace ---

class WorkspaceCreate(BaseModel):
    name: str = Field(..., max_length=255)
    type: str = Field(default="personal", max_length=20)
    settings: dict = Field(default_factory=dict)


class WorkspaceRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    type: str
    settings: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- UserProfile ---

class UserProfileRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    preferences: dict
    active_domains: list[str]
    metadata: dict

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    preferences: dict | None = None
    active_domains: list[str] | None = None
    metadata: dict | None = None
