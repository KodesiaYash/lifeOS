"""
Pydantic schemas for the connectors system.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ConnectorDefinitionCreate(BaseModel):
    connector_type: str = Field(..., max_length=100)
    name: str = Field(..., max_length=255)
    description: str | None = None
    provider: str = Field(..., max_length=100)
    auth_type: str = Field(..., max_length=50)
    config_schema: dict = Field(default_factory=dict)
    capabilities: dict = Field(default_factory=dict)


class ConnectorDefinitionRead(BaseModel):
    id: uuid.UUID
    connector_type: str
    name: str
    description: str | None
    provider: str
    auth_type: str
    config_schema: dict
    capabilities: dict
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ConnectorInstanceCreate(BaseModel):
    connector_type: str
    display_name: str = Field(..., max_length=255)
    credentials: dict = Field(default_factory=dict)
    config: dict = Field(default_factory=dict)
    sync_frequency_minutes: int | None = None


class ConnectorInstanceRead(BaseModel):
    id: uuid.UUID
    connector_type: str
    display_name: str
    config: dict
    status: str
    last_sync_at: datetime | None
    sync_frequency_minutes: int | None
    error_message: str | None
    error_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SyncLogRead(BaseModel):
    id: uuid.UUID
    instance_id: uuid.UUID
    sync_type: str
    status: str
    records_fetched: int
    records_created: int
    records_updated: int
    records_skipped: int
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None
    duration_ms: int | None

    model_config = {"from_attributes": True}
