"""
Unit tests for src/agents/schemas.py — agent request/response schemas.

Tests:
  - test_invoke_request_minimal: Minimum valid invoke request
  - test_invoke_request_with_context: Context dict and correlation_id preserved
  - test_invoke_request_defaults: context defaults to {}, correlation_id to None
  - test_invoke_response_completed: Completed response has output and metrics
  - test_invoke_response_failed: Failed response has error text
"""
import uuid

from src.agents.schemas import AgentInvokeRequest, AgentInvokeResponse


class TestAgentInvokeRequest:
    """Verify agent invocation request schema."""

    def test_invoke_request_minimal(self):
        """Minimum: agent_type + input_text."""
        req = AgentInvokeRequest(
            agent_type="health.nutrition_coach",
            input_text="Log my breakfast: 2 eggs and toast",
        )
        assert req.agent_type == "health.nutrition_coach"
        assert "eggs" in req.input_text

    def test_invoke_request_with_context(self):
        """Context and correlation_id are preserved."""
        cid = uuid.uuid4()
        req = AgentInvokeRequest(
            agent_type="test.agent",
            input_text="Hello",
            context={"key": "value"},
            correlation_id=cid,
        )
        assert req.context["key"] == "value"
        assert req.correlation_id == cid

    def test_invoke_request_defaults(self):
        """context defaults to {}, correlation_id to None."""
        req = AgentInvokeRequest(agent_type="x", input_text="y")
        assert req.context == {}
        assert req.correlation_id is None


class TestAgentInvokeResponse:
    """Verify agent invocation response schema."""

    def test_invoke_response_completed(self):
        """Completed response carries output and metrics."""
        resp = AgentInvokeResponse(
            execution_id=uuid.uuid4(),
            agent_type="health.nutrition_coach",
            status="completed",
            output_text="Logged your breakfast!",
            llm_calls=2,
            total_tokens=350,
            duration_ms=1200,
        )
        assert resp.status == "completed"
        assert resp.output_text == "Logged your breakfast!"
        assert resp.llm_calls == 2

    def test_invoke_response_failed(self):
        """Failed response has status=failed and error in output_text."""
        resp = AgentInvokeResponse(
            execution_id=uuid.uuid4(),
            agent_type="test",
            status="failed",
            output_text="Agent execution failed: timeout",
        )
        assert resp.status == "failed"
        assert "failed" in resp.output_text.lower()
