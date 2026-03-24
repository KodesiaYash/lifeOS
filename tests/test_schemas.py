"""
Tests for Pydantic schemas across modules.
"""
import uuid
from datetime import datetime, timezone

import pytest

from src.communication.schemas import InboundMessageCreate, MessageType
from src.core.schemas import TenantCreate, UserCreate, WorkspaceCreate
from src.memory.schemas import MemoryFactCreate, MemoryPacket, SemanticMemoryCreate
from src.orchestration.schemas import StepType, TriggerType, WorkflowStatus
from src.scheduling.schemas import BackgroundTaskCreate, ScheduleType, ScheduledJobCreate


class TestCoreSchemas:
    def test_tenant_create(self):
        t = TenantCreate(name="Acme Corp", slug="acme-corp")
        assert t.name == "Acme Corp"
        assert t.slug == "acme-corp"

    def test_user_create(self):
        u = UserCreate(email="alice@example.com", name="Alice")
        assert u.email == "alice@example.com"

    def test_workspace_create(self):
        w = WorkspaceCreate(name="My Workspace", type="personal")
        assert w.type == "personal"


class TestCommunicationSchemas:
    def test_inbound_message(self):
        msg = InboundMessageCreate(
            channel_type="whatsapp",
            external_user_id="123456",
            text="Hello!",
        )
        assert msg.channel_type == "whatsapp"
        assert msg.text == "Hello!"

    def test_message_type_enum(self):
        assert MessageType.TEXT == "text"
        assert MessageType.IMAGE == "image"


class TestMemorySchemas:
    def test_memory_fact_create(self):
        fact = MemoryFactCreate(
            category="dietary_preference",
            key="diet_type",
            value="vegetarian",
            domain="health",
            confidence=0.95,
            source="user_stated",
        )
        assert fact.confidence == 0.95

    def test_semantic_memory_create(self):
        mem = SemanticMemoryCreate(
            content="User prefers morning workouts",
            memory_type="preference",
            source_domain="health",
            importance=0.8,
        )
        assert mem.importance == 0.8

    def test_memory_packet(self):
        packet = MemoryPacket(
            session_context={"current_topic": "nutrition"},
            user_facts=[{"key": "diet", "value": "vegan"}],
            semantic_matches=[],
            recent_summaries=[],
            total_tokens=150,
        )
        assert packet.total_tokens == 150
        assert len(packet.user_facts) == 1


class TestOrchestrationSchemas:
    def test_workflow_status_enum(self):
        assert WorkflowStatus.PENDING == "pending"
        assert WorkflowStatus.RUNNING == "running"
        assert WorkflowStatus.COMPLETED == "completed"

    def test_step_type_enum(self):
        assert StepType.LLM_CALL == "llm_call"
        assert StepType.TOOL_CALL == "tool_call"
        assert StepType.CONDITION == "condition"

    def test_trigger_type_enum(self):
        assert TriggerType.EVENT == "event"
        assert TriggerType.SCHEDULE == "schedule"


class TestSchedulingSchemas:
    def test_scheduled_job_create(self):
        job = ScheduledJobCreate(
            name="Daily Summary",
            job_type="daily_summary",
            schedule_type=ScheduleType.CRON,
            schedule_config={"hour": 8, "minute": 0},
            handler="src.scheduling.handlers.daily_summary",
        )
        assert job.schedule_type == "cron"
        assert job.max_retries == 3

    def test_background_task_create(self):
        task = BackgroundTaskCreate(
            task_type="process_knowledge_ingestion",
            payload={"document_id": str(uuid.uuid4())},
            priority=3,
        )
        assert task.priority == 3
        assert task.max_attempts == 3
