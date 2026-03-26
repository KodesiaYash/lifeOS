"""
Workflow execution engine: runs workflow definitions step-by-step.
Supports LLM calls, tool calls, conditions, parallel steps, and event emission.

Single-user mode: No tenant_id or user_id needed.
"""
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.kernel.llm_client import LLMClient
from src.kernel.tool_registry import tool_registry
from src.orchestration.models import WorkflowExecution, WorkflowStepExecution
from src.orchestration.repository import (
    WorkflowDefinitionRepository,
    WorkflowExecutionRepository,
    WorkflowStepExecutionRepository,
)
from src.shared.time import utc_now

logger = structlog.get_logger()


class WorkflowEngine:
    """
    Executes workflow definitions step-by-step.

    Supported step types:
    - llm_call: Invoke the LLM with a prompt
    - tool_call: Invoke a registered tool
    - condition: Branch based on a condition expression
    - parallel: Run multiple sub-steps concurrently
    - wait_for_input: Pause and wait for user input
    - emit_event: Publish a platform event
    - store_memory: Store a fact or semantic memory
    - transform: Transform data between steps
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.definitions = WorkflowDefinitionRepository(session)
        self.executions = WorkflowExecutionRepository(session)
        self.steps = WorkflowStepExecutionRepository(session)
        self.llm = LLMClient()

    async def start_workflow(
        self,
        definition_id: uuid.UUID,
        initial_context: dict | None = None,
        correlation_id: uuid.UUID | None = None,
    ) -> WorkflowExecution:
        """Create and start a workflow execution."""
        definition = await self.definitions.get_by_id(definition_id)
        if definition is None:
            raise ValueError(f"Workflow definition not found: {definition_id}")

        execution = WorkflowExecution(
            definition_id=definition_id,
            correlation_id=correlation_id,
            status="running",
            current_step=0,
            context=initial_context or {},
            started_at=utc_now(),
        )
        execution = await self.executions.create(execution)

        logger.info(
            "workflow_started",
            execution_id=str(execution.id),
            definition_id=str(definition_id),
            definition_name=definition.name,
        )

        # Run the workflow
        await self._run(execution, definition.steps)
        return execution

    async def resume_workflow(self, execution_id: uuid.UUID) -> WorkflowExecution | None:
        """Resume a paused workflow execution."""
        execution = await self.executions.get_by_id(execution_id)
        if execution is None or execution.status != "paused":
            return None

        definition = await self.definitions.get_by_id(execution.definition_id)
        if definition is None:
            return None

        await self.executions.update_status(execution_id, "running")
        await self._run(execution, definition.steps)
        return execution

    async def _run(self, execution: WorkflowExecution, steps_config: dict) -> None:
        """Execute workflow steps sequentially."""
        steps = steps_config if isinstance(steps_config, list) else steps_config.get("steps", [])

        while execution.current_step < len(steps):
            step_config = steps[execution.current_step]
            step_type = step_config.get("type", "unknown")

            # Create step execution record
            step_exec = WorkflowStepExecution(
                execution_id=execution.id,
                step_index=execution.current_step,
                step_type=step_type,
                step_config=step_config,
                status="running",
                input_data={"context": execution.context},
                started_at=utc_now(),
            )
            step_exec = await self.steps.create(step_exec)

            try:
                start = datetime.now(timezone.utc)
                result = await self._execute_step(step_type, step_config, execution)
                duration = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)

                # Update step execution
                step_exec.status = "completed"
                step_exec.output_data = result
                step_exec.completed_at = utc_now()
                step_exec.duration_ms = duration
                await self.session.flush()

                # Merge step result into execution context
                if result:
                    execution.context = {**execution.context, **result}

                # Check if workflow should pause
                if step_type == "wait_for_input":
                    await self.executions.update_status(execution.id, "paused", current_step=execution.current_step)
                    return

                execution.current_step += 1
                await self.session.flush()

            except Exception as e:
                step_exec.status = "failed"
                step_exec.error_message = str(e)
                step_exec.completed_at = utc_now()
                await self.session.flush()

                await self.executions.update_status(
                    execution.id, "failed",
                    error_message=str(e),
                    completed_at=utc_now(),
                )
                logger.exception("workflow_step_failed", execution_id=str(execution.id), step=execution.current_step)
                return

        # Workflow completed
        await self.executions.update_status(
            execution.id, "completed",
            result=execution.context,
            completed_at=utc_now(),
        )
        logger.info("workflow_completed", execution_id=str(execution.id))

    async def _execute_step(
        self, step_type: str, config: dict, execution: WorkflowExecution
    ) -> dict:
        """Execute a single workflow step based on its type."""
        if step_type == "llm_call":
            return await self._step_llm_call(config, execution)
        elif step_type == "tool_call":
            return await self._step_tool_call(config, execution)
        elif step_type == "condition":
            return await self._step_condition(config, execution)
        elif step_type == "emit_event":
            return await self._step_emit_event(config, execution)
        elif step_type == "transform":
            return await self._step_transform(config, execution)
        elif step_type == "wait_for_input":
            return {}
        else:
            logger.warning("unknown_step_type", step_type=step_type)
            return {}

    async def _step_llm_call(self, config: dict, execution: WorkflowExecution) -> dict:
        """Execute an LLM call step."""
        prompt = config.get("prompt", "")
        # Simple variable substitution from context
        for key, value in execution.context.items():
            prompt = prompt.replace(f"{{{key}}}", str(value))

        messages = [
            {"role": "system", "content": config.get("system_prompt", "You are a helpful assistant.")},
            {"role": "user", "content": prompt},
        ]
        response = await self.llm.complete(
            messages=messages,
            model=config.get("model"),
            temperature=config.get("temperature"),
        )
        output_key = config.get("output_key", "llm_response")
        return {output_key: response}

    async def _step_tool_call(self, config: dict, execution: WorkflowExecution) -> dict:
        """Execute a tool call step."""
        tool_id = config.get("tool_id", "")
        params = config.get("parameters", {})
        # Substitute context variables into parameters
        resolved_params = {}
        for k, v in params.items():
            if isinstance(v, str) and v.startswith("{") and v.endswith("}"):
                ctx_key = v[1:-1]
                resolved_params[k] = execution.context.get(ctx_key, v)
            else:
                resolved_params[k] = v

        result = await tool_registry.invoke(tool_id, **resolved_params)
        output_key = config.get("output_key", "tool_result")
        return {output_key: result.model_dump()}

    async def _step_condition(self, config: dict, execution: WorkflowExecution) -> dict:
        """Evaluate a condition and adjust workflow flow."""
        # Simple condition evaluation based on context values
        condition_key = config.get("condition_key", "")
        expected_value = config.get("expected_value")
        actual_value = execution.context.get(condition_key)

        condition_met = actual_value == expected_value
        return {"condition_result": condition_met}

    async def _step_emit_event(self, config: dict, execution: WorkflowExecution) -> dict:
        """Emit a platform event."""
        from src.events.bus import event_bus
        from src.events.schemas import PlatformEvent

        event = PlatformEvent(
            event_type=config.get("event_type", "workflow.step_event"),
            event_category=config.get("category", "system"),
            domain=config.get("domain"),
            correlation_id=execution.correlation_id,
            payload=config.get("payload", {}),
            source="workflow",
        )
        await event_bus.publish(event, session=self.session)
        return {"event_emitted": str(event.id)}

    async def _step_transform(self, config: dict, execution: WorkflowExecution) -> dict:
        """Transform data between steps (simple key mapping)."""
        mappings = config.get("mappings", {})
        result = {}
        for target_key, source_key in mappings.items():
            result[target_key] = execution.context.get(source_key)
        return result
