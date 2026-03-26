"""
Pydantic schemas for the agent system.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AgentDefinitionCreate(BaseModel):
    agent_type: str = Field(..., max_length=100)
    name: str = Field(..., max_length=255)
    description: str | None = None
    domain: str | None = None
    system_prompt: str
    model_preference: str | None = None
    temperature: float = 0.7
    max_tokens: int = 2048
    tools: list[str] = Field(default_factory=list)
    capabilities: dict = Field(default_factory=dict)


class AgentDefinitionRead(BaseModel):
    id: uuid.UUID
    agent_type: str
    name: str
    description: str | None
    domain: str | None
    system_prompt: str
    model_preference: str | None
    temperature: float
    max_tokens: int
    tools: list[str]
    capabilities: dict
    active: bool
    version: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentExecutionRead(BaseModel):
    id: uuid.UUID
    agent_type: str
    status: str
    input_data: dict
    output_data: dict | None
    tool_calls: list[dict]
    llm_calls: int
    total_tokens: int
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    duration_ms: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentInvokeRequest(BaseModel):
    """Request to invoke an agent."""

    agent_type: str
    input_text: str
    context: dict = Field(default_factory=dict)
    correlation_id: uuid.UUID | None = None


class AgentInvokeResponse(BaseModel):
    """Response from an agent invocation."""

    execution_id: uuid.UUID
    agent_type: str
    status: str
    output_text: str | None = None
    tool_calls: list[dict] = Field(default_factory=list)
    llm_calls: int = 0
    total_tokens: int = 0
    duration_ms: int | None = None
