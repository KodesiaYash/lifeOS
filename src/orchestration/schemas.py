"""
Pydantic schemas for workflow orchestration.
"""
import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class WorkflowStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepType(StrEnum):
    LLM_CALL = "llm_call"
    TOOL_CALL = "tool_call"
    CONDITION = "condition"
    PARALLEL = "parallel"
    WAIT_FOR_INPUT = "wait_for_input"
    EMIT_EVENT = "emit_event"
    STORE_MEMORY = "store_memory"
    TRANSFORM = "transform"


class TriggerType(StrEnum):
    EVENT = "event"
    SCHEDULE = "schedule"
    MANUAL = "manual"
    WEBHOOK = "webhook"


class WorkflowDefinitionCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None
    domain: str | None = None
    trigger_type: TriggerType
    trigger_config: dict = Field(default_factory=dict)
    steps: list[dict] = Field(...)


class WorkflowDefinitionRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    description: str | None
    domain: str | None
    version: int
    trigger_type: str
    trigger_config: dict
    steps: dict
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkflowExecutionRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    definition_id: uuid.UUID
    status: str
    current_step: int
    context: dict
    result: dict | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkflowStepExecutionRead(BaseModel):
    id: uuid.UUID
    execution_id: uuid.UUID
    step_index: int
    step_type: str
    status: str
    input_data: dict | None
    output_data: dict | None
    error_message: str | None
    duration_ms: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
