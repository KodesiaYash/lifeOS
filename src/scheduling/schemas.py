"""
Pydantic schemas for the scheduling system.
"""
import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ScheduleType(StrEnum):
    CRON = "cron"
    INTERVAL = "interval"
    DATE = "date"


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class ScheduledJobCreate(BaseModel):
    name: str = Field(..., max_length=255)
    job_type: str = Field(..., max_length=50)
    schedule_type: ScheduleType
    schedule_config: dict  # e.g., {"hour": 8, "minute": 0} for cron
    handler: str = Field(..., max_length=255)
    handler_args: dict = Field(default_factory=dict)
    domain: str | None = None
    timezone: str = "UTC"
    max_retries: int = 3


class ScheduledJobRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    name: str
    job_type: str
    schedule_type: str
    schedule_config: dict
    handler: str
    domain: str | None
    timezone: str
    active: bool
    last_run_at: datetime | None
    next_run_at: datetime | None
    run_count: int
    error_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class BackgroundTaskCreate(BaseModel):
    task_type: str
    payload: dict = Field(default_factory=dict)
    priority: int = 5
    max_attempts: int = 3
    scheduled_at: datetime | None = None
    correlation_id: uuid.UUID | None = None


class BackgroundTaskRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID | None
    task_type: str
    status: str
    priority: int
    payload: dict
    result: dict | None
    error_message: str | None
    attempts: int
    max_attempts: int
    scheduled_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
