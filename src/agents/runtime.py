"""
Agent runtime: executes agent definitions with ReAct-style tool calling loops.
"""

import json
import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.models import AgentExecution
from src.agents.repository import AgentDefinitionRepository, AgentExecutionRepository
from src.agents.schemas import AgentInvokeRequest, AgentInvokeResponse
from src.kernel.llm_client import LLMClient
from src.kernel.tool_registry import tool_registry
from src.shared.time import utc_now

logger = structlog.get_logger()

MAX_REACT_ITERATIONS = 5


class AgentRuntime:
    """
    Executes agent definitions with ReAct-style tool calling.

    Flow:
    1. Load agent definition
    2. Build messages (system prompt + context + user input)
    3. ReAct loop: LLM call → tool calls → append results → repeat
    4. Return final response
    5. Persist execution record
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.definitions = AgentDefinitionRepository(session)
        self.executions = AgentExecutionRepository(session)
        self.llm = LLMClient()

    async def invoke(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        request: AgentInvokeRequest,
    ) -> AgentInvokeResponse:
        """Invoke an agent by type."""
        # Load definition
        definition = await self.definitions.get_by_type(request.agent_type)
        if definition is None:
            return AgentInvokeResponse(
                execution_id=uuid.uuid4(),
                agent_type=request.agent_type,
                status="failed",
                output_text=f"Agent type not found: {request.agent_type}",
            )

        # Create execution record
        execution = AgentExecution(
            tenant_id=tenant_id,
            user_id=user_id,
            agent_type=request.agent_type,
            correlation_id=request.correlation_id,
            status="running",
            input_data={"text": request.input_text, "context": request.context},
            started_at=utc_now(),
        )
        execution = await self.executions.create(execution)

        start_time = datetime.now(UTC)
        total_tokens = 0
        llm_calls = 0
        all_tool_calls: list[dict] = []

        try:
            # Build messages
            messages: list[dict[str, str]] = [
                {"role": "system", "content": definition.system_prompt},
            ]

            # Add context if provided
            if request.context:
                context_str = json.dumps(request.context, default=str)
                messages.append({"role": "system", "content": f"Context: {context_str}"})

            messages.append({"role": "user", "content": request.input_text})

            # Get tools for this agent
            tools = []
            if definition.tools:
                all_tools = tool_registry.get_openai_tools(domain=definition.domain)
                tools = [t for t in all_tools if t["function"]["name"] in definition.tools]

            # ReAct loop
            output_text = ""
            for _iteration in range(MAX_REACT_ITERATIONS):
                if tools:
                    result = await self.llm.complete_with_tools(
                        messages=messages,
                        tools=tools,
                        model=definition.model_preference,
                        temperature=definition.temperature,
                    )
                    llm_calls += 1
                    total_tokens += result["usage"]["prompt_tokens"] + result["usage"]["completion_tokens"]

                    if not result["tool_calls"]:
                        output_text = result["content"] or ""
                        break

                    # Execute tool calls
                    for tc in result["tool_calls"]:
                        tool_args = json.loads(tc["function"]["arguments"])
                        tool_result = await tool_registry.invoke(tc["function"]["name"], **tool_args)
                        all_tool_calls.append(
                            {
                                "tool_id": tc["function"]["name"],
                                "arguments": tool_args,
                                "result": tool_result.model_dump(),
                            }
                        )

                        messages.append({"role": "assistant", "content": None, "tool_calls": [tc]})
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tc["id"],
                                "content": json.dumps(tool_result.model_dump(), default=str),
                            }
                        )
                else:
                    output_text = await self.llm.complete(
                        messages=messages,
                        model=definition.model_preference,
                        temperature=definition.temperature,
                        max_tokens=definition.max_tokens,
                    )
                    llm_calls += 1
                    break

            duration_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)

            # Update execution record
            await self.executions.update_status(
                execution.id,
                "completed",
                output_data={"text": output_text},
                tool_calls=all_tool_calls,
                llm_calls=llm_calls,
                total_tokens=total_tokens,
                completed_at=utc_now(),
                duration_ms=duration_ms,
            )

            logger.info(
                "agent_execution_complete",
                execution_id=str(execution.id),
                agent_type=request.agent_type,
                llm_calls=llm_calls,
                tool_calls=len(all_tool_calls),
                duration_ms=duration_ms,
            )

            return AgentInvokeResponse(
                execution_id=execution.id,
                agent_type=request.agent_type,
                status="completed",
                output_text=output_text,
                tool_calls=all_tool_calls,
                llm_calls=llm_calls,
                total_tokens=total_tokens,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
            await self.executions.update_status(
                execution.id,
                "failed",
                error_message=str(e),
                completed_at=utc_now(),
                duration_ms=duration_ms,
            )
            logger.exception("agent_execution_failed", execution_id=str(execution.id))

            return AgentInvokeResponse(
                execution_id=execution.id,
                agent_type=request.agent_type,
                status="failed",
                output_text=f"Agent execution failed: {e}",
                duration_ms=duration_ms,
            )
