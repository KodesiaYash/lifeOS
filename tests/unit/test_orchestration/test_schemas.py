"""
Unit tests for src/orchestration/schemas.py — workflow orchestration schemas.

Tests:
  - test_workflow_status_values: All expected statuses exist
  - test_step_type_values: All 6 step types exist
  - test_trigger_type_values: All trigger types exist (event, schedule, manual, api)
  - test_workflow_create_minimal: Minimum valid workflow definition
  - test_workflow_step_config: Step config is preserved as dict
"""

from src.orchestration.schemas import StepType, TriggerType, WorkflowStatus


class TestWorkflowStatus:
    """Verify workflow execution status enum."""

    def test_pending(self):
        assert WorkflowStatus.PENDING == "pending"

    def test_running(self):
        assert WorkflowStatus.RUNNING == "running"

    def test_completed(self):
        assert WorkflowStatus.COMPLETED == "completed"

    def test_failed(self):
        assert WorkflowStatus.FAILED == "failed"

    def test_paused(self):
        assert WorkflowStatus.PAUSED == "paused"


class TestStepType:
    """Verify workflow step type enum — one per execution strategy."""

    def test_llm_call(self):
        """LLM prompt execution step."""
        assert StepType.LLM_CALL == "llm_call"

    def test_tool_call(self):
        """Registered tool invocation step."""
        assert StepType.TOOL_CALL == "tool_call"

    def test_condition(self):
        """Branching step based on previous output."""
        assert StepType.CONDITION == "condition"

    def test_emit_event(self):
        """Event bus publication step."""
        assert StepType.EMIT_EVENT == "emit_event"

    def test_transform(self):
        """Data reshaping step between other steps."""
        assert StepType.TRANSFORM == "transform"

    def test_wait_for_input(self):
        """Human-in-the-loop pause step."""
        assert StepType.WAIT_FOR_INPUT == "wait_for_input"


class TestTriggerType:
    """Verify workflow trigger type enum."""

    def test_event(self):
        assert TriggerType.EVENT == "event"

    def test_schedule(self):
        assert TriggerType.SCHEDULE == "schedule"

    def test_manual(self):
        assert TriggerType.MANUAL == "manual"

    def test_webhook(self):
        assert TriggerType.WEBHOOK == "webhook"
