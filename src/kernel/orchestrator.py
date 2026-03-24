"""
Global orchestrator: the central brain that processes every inbound message.
Routes through: intent classification → memory assembly → retrieval → tool execution → response generation.
"""
import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.events.bus import event_bus
from src.events.schemas import PlatformEvent
from src.kernel.llm_client import LLMClient
from src.kernel.tool_registry import tool_registry
from src.memory.assembler import MemoryAssembler
from src.memory.short_term import ShortTermMemory
from src.retrieval.coordinator import RetrievalCoordinator
from src.retrieval.schemas import RetrievalRequest, RetrievalStrategy

logger = structlog.get_logger()


class OrchestratorContext:
    """Accumulated context for a single orchestration turn."""

    def __init__(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        user_message: str,
        conversation_id: uuid.UUID | None = None,
        channel_type: str = "rest_api",
        correlation_id: uuid.UUID | None = None,
    ) -> None:
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.user_message = user_message
        self.conversation_id = conversation_id
        self.channel_type = channel_type
        self.correlation_id = correlation_id or uuid.uuid4()

        # Populated during orchestration
        self.intent: dict | None = None
        self.memory_context: dict | None = None
        self.retrieval_context: list[dict] | None = None
        self.tool_results: list[dict] | None = None
        self.response_text: str | None = None


class GlobalOrchestrator:
    """
    The central orchestration engine that handles every user interaction.

    Pipeline:
    1. Classify intent (determine domain, action, entities)
    2. Assemble memory context (short-term + structured + semantic)
    3. Retrieve relevant knowledge (hybrid RAG)
    4. Execute tool calls if needed (ReAct loop)
    5. Generate response
    6. Emit events
    7. Update memory
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.llm = LLMClient()
        self.memory_assembler = MemoryAssembler(session)
        self.short_term = ShortTermMemory()
        self.retrieval = RetrievalCoordinator(session)

    async def process(self, ctx: OrchestratorContext) -> str:
        """Run the full orchestration pipeline for an inbound message."""
        logger.info(
            "orchestration_start",
            correlation_id=str(ctx.correlation_id),
            channel=ctx.channel_type,
            message_preview=ctx.user_message[:80],
        )

        try:
            # 1. Classify intent
            ctx.intent = await self._classify_intent(ctx)

            # 2. Assemble memory
            memory_packet = await self.memory_assembler.assemble(
                tenant_id=ctx.tenant_id,
                user_id=ctx.user_id,
                domain=ctx.intent.get("domain"),
            )
            ctx.memory_context = memory_packet.model_dump()

            # 3. Retrieve relevant knowledge
            retrieval_response = await self.retrieval.retrieve(
                RetrievalRequest(
                    tenant_id=ctx.tenant_id,
                    user_id=ctx.user_id,
                    query=ctx.user_message,
                    domains=[ctx.intent["domain"]] if ctx.intent.get("domain") else None,
                    strategy=RetrievalStrategy.HYBRID,
                    max_results=10,
                )
            )
            ctx.retrieval_context = [r.model_dump() for r in retrieval_response.results]

            # 4. Generate response (with optional tool calls)
            ctx.response_text = await self._generate_response(ctx)

            # 5. Emit events
            await self._emit_events(ctx)

            # 6. Update short-term memory
            await self.short_term.add_to_message_history(
                ctx.tenant_id, ctx.user_id, "user", ctx.user_message
            )
            await self.short_term.add_to_message_history(
                ctx.tenant_id, ctx.user_id, "assistant", ctx.response_text
            )

            logger.info(
                "orchestration_complete",
                correlation_id=str(ctx.correlation_id),
                intent_domain=ctx.intent.get("domain"),
                response_length=len(ctx.response_text),
            )
            return ctx.response_text

        except Exception:
            logger.exception("orchestration_error", correlation_id=str(ctx.correlation_id))
            return "I'm sorry, something went wrong while processing your request. Please try again."

    async def _classify_intent(self, ctx: OrchestratorContext) -> dict:
        """
        Classify the user's intent: domain, action, entities, confidence.
        TODO: Replace stub with LLM-based intent classification.
        """
        logger.debug("intent_classification_stub", message=ctx.user_message[:50])
        return {
            "domain": None,
            "action": "general_chat",
            "entities": {},
            "confidence": 0.5,
        }

    async def _generate_response(self, ctx: OrchestratorContext) -> str:
        """
        Build the full prompt with context and generate a response.
        Supports ReAct-style tool calling loop.
        """
        # Build system prompt
        system_prompt = self._build_system_prompt(ctx)

        # Build messages
        message_history = await self.short_term.get_message_history(ctx.tenant_id, ctx.user_id)
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(message_history[-10:])  # Last 10 turns
        messages.append({"role": "user", "content": ctx.user_message})

        # Get available tools
        tools = tool_registry.get_openai_tools(domain=ctx.intent.get("domain") if ctx.intent else None)

        if tools:
            # Tool-calling loop (max 3 iterations)
            for _ in range(3):
                result = await self.llm.complete_with_tools(messages=messages, tools=tools)

                if not result["tool_calls"]:
                    return result["content"] or ""

                # Execute tool calls
                for tc in result["tool_calls"]:
                    import json
                    tool_args = json.loads(tc["function"]["arguments"])
                    tool_result = await tool_registry.invoke(tc["function"]["name"], **tool_args)

                    messages.append({"role": "assistant", "content": None, "tool_calls": [tc]})
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps(tool_result.model_dump(), default=str),
                    })

            # Final completion after tool calls
            return await self.llm.complete(messages=messages)
        else:
            return await self.llm.complete(messages=messages)

    def _build_system_prompt(self, ctx: OrchestratorContext) -> str:
        """Assemble the system prompt with memory and retrieval context."""
        parts = [
            "You are an AI life assistant that helps users manage all aspects of their life.",
            "Be helpful, concise, and proactive. Use the user's context to personalize responses.",
        ]

        # Add memory context
        if ctx.memory_context:
            facts = ctx.memory_context.get("user_facts", [])
            if facts:
                fact_lines = [f"- {f['key']}: {f['value']}" for f in facts[:20]]
                parts.append(f"\n## What you know about this user:\n" + "\n".join(fact_lines))

            summaries = ctx.memory_context.get("recent_summaries", [])
            if summaries:
                parts.append(f"\n## Recent conversation context:\n" + "\n".join(summaries[:3]))

        # Add retrieval context
        if ctx.retrieval_context:
            context_texts = [r["content"] for r in ctx.retrieval_context[:5]]
            if context_texts:
                parts.append(f"\n## Relevant knowledge:\n" + "\n---\n".join(context_texts))

        return "\n\n".join(parts)

    async def _emit_events(self, ctx: OrchestratorContext) -> None:
        """Emit platform events for this interaction."""
        event = PlatformEvent(
            tenant_id=ctx.tenant_id,
            user_id=ctx.user_id,
            event_type="system.message_processed",
            event_category="system",
            correlation_id=ctx.correlation_id,
            payload={
                "channel_type": ctx.channel_type,
                "intent": ctx.intent,
                "response_length": len(ctx.response_text) if ctx.response_text else 0,
            },
            source="system",
        )
        await event_bus.publish(event, session=self.session)
