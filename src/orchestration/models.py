"""
SQLAlchemy models for workflow orchestration.

Single-user mode: No tenant_id or user_id references.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.base_model import TimestampedBase
from src.shared.sql_types import JSONType, UUIDType


class WorkflowDefinition(TimestampedBase):
    """Reusable workflow template definitions."""

    __tablename__ = "orch_workflow_definitions"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    domain: Mapped[str | None] = mapped_column(String(100), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)
    trigger_config: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    steps: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    active: Mapped[bool] = mapped_column(Integer, nullable=False, default=True)


class WorkflowExecution(TimestampedBase):
    """Runtime instance of a workflow execution."""

    __tablename__ = "orch_workflow_executions"

    definition_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("orch_workflow_definitions.id"), nullable=False
    )
    correlation_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default="pending")
    current_step: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    context: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    result: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WorkflowStepExecution(TimestampedBase):
    """Individual step execution within a workflow."""

    __tablename__ = "orch_workflow_step_executions"

    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("orch_workflow_executions.id"), nullable=False, index=True
    )
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    step_type: Mapped[str] = mapped_column(String(50), nullable=False)
    step_config: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default="pending")
    input_data: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    output_data: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
