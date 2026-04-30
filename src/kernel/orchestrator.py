"""
Global orchestrator: the central brain that processes every inbound message.
Routes through: intent classification -> memory assembly -> retrieval -> tool execution -> response generation.

Single-user mode: No tenant_id or user_id needed.
"""

from __future__ import annotations

import json
import uuid
from typing import TYPE_CHECKING

import structlog

from src.agents.registry import AgentRegistry, agent_registry
from src.communication.schemas import ContentType
from src.config import settings
from src.domains.loader import get_loaded_plugin
from src.events.bus import EventBus, event_bus
from src.events.schemas import PlatformEvent
from src.kernel.llm_client import LLMClient
from src.kernel.tool_registry import ToolRegistry, tool_registry
from src.memory.assembler import MemoryAssembler
from src.memory.service import GENERAL_MEMORY_NAMESPACE, MemoryService
from src.memory.short_term import ShortTermMemory
from src.retrieval.coordinator import RetrievalCoordinator
from src.retrieval.schemas import RetrievalRequest, RetrievalStrategy

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.domains.plugin import DomainPlugin
    from src.memory.schemas import ScopedMemoryPacket

logger = structlog.get_logger()


def _has_configured_llm() -> bool:
    return any(
        [
            settings.OPENAI_API_KEY,
            settings.ANTHROPIC_API_KEY,
            settings.GEMINI_API_KEY,
            settings.GROQ_API_KEY,
            settings.MISTRAL_API_KEY,
            settings.AZURE_API_KEY,
        ]
    )


class OrchestratorContext:
    """Accumulated context for a single orchestration turn."""

    def __init__(
        self,
        user_message: str,
        conversation_id: uuid.UUID | None = None,
        channel_type: str = "rest_api",
        correlation_id: uuid.UUID | None = None,
        session_id: str | None = None,
        message_id: uuid.UUID | None = None,
        bot_id: str | None = None,
        target_domain: str | None = None,
        channel_user_id: str | None = None,
        external_chat_id: str | None = None,
        user_name: str | None = None,
        content_type: str = ContentType.TEXT,
    ) -> None:
        self.user_message = user_message
        self.conversation_id = conversation_id
        self.channel_type = channel_type
        self.correlation_id = correlation_id or uuid.uuid4()
        self.session_id = session_id
        self.message_id = message_id
        self.bot_id = bot_id
        self.target_domain = target_domain
        self.channel_user_id = channel_user_id
        self.external_chat_id = external_chat_id
        self.user_name = user_name
        self.content_type = content_type

        # Populated during orchestration
        self.intent: dict | None = None
        self.memory_context: dict | None = None
        self.retrieval_context: list[dict] | None = None
        self.tool_results: list[dict] | None = None
        self.response_text: str | None = None
        self.scoped_memory_context: ScopedMemoryPacket | None = None


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

    def __init__(
        self,
        session: AsyncSession,
        *,
        llm: LLMClient | None = None,
        memory_assembler: MemoryAssembler | None = None,
        memory_service: MemoryService | None = None,
        short_term: ShortTermMemory | None = None,
        retrieval: RetrievalCoordinator | None = None,
        event_bus_instance: EventBus | None = None,
        tool_registry_instance: ToolRegistry | None = None,
        agent_registry_instance: AgentRegistry | None = None,
        domain_plugins: dict[str, DomainPlugin] | None = None,
    ) -> None:
        self.session = session
        self.llm = llm or LLMClient()
        self.memory_assembler = memory_assembler or MemoryAssembler(session)
        self.memory_service = memory_service or MemoryService(session)
        self.short_term = short_term or ShortTermMemory()
        self.retrieval = retrieval or RetrievalCoordinator(session)
        self.event_bus = event_bus_instance or event_bus
        self.tool_registry = tool_registry_instance or tool_registry
        self.agent_registry = agent_registry_instance or agent_registry
        self.domain_plugins = domain_plugins

    async def process(self, ctx: OrchestratorContext) -> str:
        """Run the full orchestration pipeline for an inbound message."""
        logger.info(
            "orchestration_start",
            correlation_id=str(ctx.correlation_id),
            channel=ctx.channel_type,
            message_preview=ctx.user_message[:80],
        )

        try:
            ctx.intent = await self._classify_intent(ctx)
            await self._emit_ingress_event(ctx)
            await self._capture_memory(ctx)
            await self._assemble_memory(ctx)
            ctx.retrieval_context = await self._retrieve_context(ctx)
            ctx.response_text = await self._generate_response(ctx)
            await self._emit_events(ctx)

            await self.short_term.add_to_message_history("user", ctx.user_message, session_id=ctx.session_id)
            await self.short_term.add_to_message_history("assistant", ctx.response_text, session_id=ctx.session_id)

            logger.info(
                "orchestration_complete",
                correlation_id=str(ctx.correlation_id),
                intent_domain=ctx.intent.get("domain") if ctx.intent else None,
                response_length=len(ctx.response_text),
            )
            return ctx.response_text

        except Exception:
            logger.exception("orchestration_error", correlation_id=str(ctx.correlation_id))
            return "I'm sorry, something went wrong while processing your request. Please try again."

    async def _classify_intent(self, ctx: OrchestratorContext) -> dict:
        """Resolve domain intent from the explicit communication route or fall back to generic chat."""
        if ctx.target_domain:
            plugin = self._get_plugin(ctx.target_domain)
            intent = {
                "domain": ctx.target_domain,
                "action": "domain_chat",
                "entities": {},
                "confidence": 1.0,
                "mode": "domain_entrypoint",
                "bot_id": ctx.bot_id,
                "memory_namespace": ctx.target_domain,
                "general_namespace": GENERAL_MEMORY_NAMESPACE,
            }
            if plugin is not None:
                direct_tool = plugin.resolve_direct_tool(ctx.user_message)
                if direct_tool is not None:
                    tool_id, tool_args = direct_tool
                    intent.update(
                        {
                            "action": "direct_tool",
                            "direct_tool": tool_id,
                            "direct_tool_args": tool_args,
                            "entities": tool_args,
                        }
                    )
            logger.debug("intent_classification_target_domain", domain=ctx.target_domain, action=intent["action"])
            return intent

        logger.debug("intent_classification_stub", message=ctx.user_message[:50])
        return {
            "domain": None,
            "action": "general_chat",
            "entities": {},
            "confidence": 0.5,
        }

    async def _capture_memory(self, ctx: OrchestratorContext) -> None:
        """Capture explicit durable facts before assembling the prompt."""
        if not ctx.intent or not ctx.intent.get("domain") or not ctx.user_message.strip():
            return

        plugin = self._get_plugin(ctx.intent["domain"])
        if plugin is None:
            return

        await plugin.capture_memory(
            self.session,
            user_message=ctx.user_message,
            user_name=ctx.user_name,
            domain_namespace=ctx.intent.get("memory_namespace") or ctx.intent["domain"],
            general_namespace=ctx.intent.get("general_namespace") or GENERAL_MEMORY_NAMESPACE,
        )

    async def _assemble_memory(self, ctx: OrchestratorContext) -> None:
        """Assemble shared plus domain-scoped memory whenever a domain is resolved."""
        if ctx.intent and ctx.intent.get("domain"):
            ctx.scoped_memory_context = await self.memory_service.retrieve_scoped_context(
                namespace=ctx.intent.get("memory_namespace") or ctx.intent["domain"],
                query=ctx.user_message,
                session_id=ctx.session_id,
                general_namespace=ctx.intent.get("general_namespace") or GENERAL_MEMORY_NAMESPACE,
            )
            ctx.memory_context = ctx.scoped_memory_context.model_dump()
            return

        memory_packet = await self.memory_assembler.assemble(
            domain=ctx.intent.get("domain") if ctx.intent else None,
            session_id=ctx.session_id,
        )
        ctx.memory_context = memory_packet.model_dump()

    async def _retrieve_context(self, ctx: OrchestratorContext) -> list[dict]:
        """Retrieve extra context through the platform retrieval coordinator."""
        request = RetrievalRequest(
            query=ctx.user_message,
            domains=[ctx.intent["domain"]] if ctx.intent and ctx.intent.get("domain") else None,
            strategy=RetrievalStrategy.HYBRID,
            max_results=10,
        )

        if ctx.intent and ctx.intent.get("domain"):
            request = RetrievalRequest(
                query=ctx.user_message,
                domains=[
                    ctx.intent.get("general_namespace") or GENERAL_MEMORY_NAMESPACE,
                    ctx.intent.get("memory_namespace") or ctx.intent["domain"],
                ],
                strategy=RetrievalStrategy.MEMORY_ONLY,
                max_results=6,
            )

        try:
            retrieval_response = await self.retrieval.retrieve(request)
        except Exception:
            logger.exception("retrieval_error", correlation_id=str(ctx.correlation_id))
            return []

        return [result.model_dump() for result in retrieval_response.results]

    async def _generate_response(self, ctx: OrchestratorContext) -> str:
        """Build the prompt, invoke tools if needed, and return the reply text."""
        if ctx.content_type != ContentType.TEXT:
            return "Stuur me een tekstbericht in het Nederlands en ik help je oefenen."

        direct_tool_id = ctx.intent.get("direct_tool") if ctx.intent else None
        if direct_tool_id:
            tool_result = await self.tool_registry.invoke(
                direct_tool_id,
                **(ctx.intent.get("direct_tool_args") or {}),
            )
            ctx.tool_results = [tool_result.model_dump()]
            return self._render_direct_tool_response(ctx, tool_result.model_dump())

        if not _has_configured_llm():
            return self._offline_fallback_message(ctx)

        system_prompt = self._build_system_prompt(ctx)
        message_history = await self.short_term.get_message_history(ctx.session_id)
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(message_history[-10:])
        messages.append({"role": "user", "content": ctx.user_message})

        tools = self.tool_registry.get_openai_tools(domain=ctx.intent.get("domain") if ctx.intent else None)
        if tools:
            for _ in range(3):
                result = await self.llm.complete_with_tools(messages=messages, tools=tools)
                if not result["tool_calls"]:
                    return result["content"] or ""

                for tool_call in result["tool_calls"]:
                    tool_args = json.loads(tool_call["function"]["arguments"])
                    tool_result = await self.tool_registry.invoke(tool_call["function"]["name"], **tool_args)
                    messages.append({"role": "assistant", "content": None, "tool_calls": [tool_call]})
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": json.dumps(tool_result.model_dump(), default=str),
                        }
                    )

            return await self.llm.complete(messages=messages)

        return await self.llm.complete(messages=messages)

    def _build_system_prompt(self, ctx: OrchestratorContext) -> str:
        """Assemble the system prompt with agent instructions, memory, and retrieval context."""
        parts = [self._base_system_prompt(ctx)]

        if ctx.memory_context:
            if "general_facts" in ctx.memory_context and "scoped_facts" in ctx.memory_context:
                self._append_scoped_memory_context(parts, ctx)
            else:
                facts = ctx.memory_context.get("user_facts", [])
                if facts:
                    fact_lines = [f"- {fact['key']}: {fact['value']}" for fact in facts[:20]]
                    parts.append("## What you know about this user:\n" + "\n".join(fact_lines))

                summaries = ctx.memory_context.get("recent_summaries", [])
                if summaries:
                    parts.append("## Recent conversation context:\n" + "\n".join(summaries[:3]))

        if ctx.retrieval_context:
            context_texts = [item["content"] for item in ctx.retrieval_context[:5] if item.get("content")]
            if context_texts:
                parts.append("## Relevant knowledge:\n" + "\n---\n".join(context_texts))

        return "\n\n".join(parts)

    def _append_scoped_memory_context(self, parts: list[str], ctx: OrchestratorContext) -> None:
        memory_context = ctx.memory_context or {}
        general_facts = memory_context.get("general_facts", [])
        scoped_facts = memory_context.get("scoped_facts", [])
        general_semantic = memory_context.get("general_semantic_memories", [])
        scoped_semantic = memory_context.get("scoped_semantic_memories", [])
        summaries = memory_context.get("recent_summaries", [])
        session_context = memory_context.get("session_context", {})
        domain = ctx.intent.get("domain") if ctx.intent else "domain"

        if general_facts:
            parts.append(
                "## General memory:\n" + "\n".join(f"- {fact['key']}: {fact['value']}" for fact in general_facts[:8])
            )

        if scoped_facts:
            parts.append(
                f"## {domain} memory:\n" + "\n".join(f"- {fact['key']}: {fact['value']}" for fact in scoped_facts[:12])
            )

        if general_semantic:
            parts.append(
                "## Relevant general notes:\n"
                + "\n".join(f"- {memory['content']}" for memory in general_semantic[:4] if memory.get("content"))
            )

        if scoped_semantic:
            parts.append(
                f"## Relevant {domain} notes:\n"
                + "\n".join(f"- {memory['content']}" for memory in scoped_semantic[:6] if memory.get("content"))
            )

        if summaries:
            parts.append("## Recent summaries:\n" + "\n".join(f"- {summary}" for summary in summaries[:3]))

        if session_context:
            parts.append(f"## Session context:\n{session_context}")

    def _base_system_prompt(self, ctx: OrchestratorContext) -> str:
        domain = ctx.intent.get("domain") if ctx.intent else None
        if domain:
            domain_agents = self.agent_registry.list_agents(domain=domain)
            if domain_agents:
                return domain_agents[0].system_prompt
            return f"You are a helpful assistant focused on the {domain} domain. Be concise and practical."

        return (
            "You are an AI life assistant that helps users manage all aspects of their life. "
            "Be helpful, concise, and proactive. Use the user's context to personalize responses."
        )

    def _offline_fallback_message(self, ctx: OrchestratorContext) -> str:
        domain = ctx.intent.get("domain") if ctx.intent else None
        if domain == "dutch_tutor":
            return (
                "Ik ben klaar om te helpen. Stuur één woord zoals 'huis' of 'boek' "
                "voor de lokale vertaalmodus, of configureer een LLM API key voor vrijere tutorchat."
            )
        return "No LLM provider is configured yet. Add an API key to enable open-ended chat responses."

    def _render_direct_tool_response(self, ctx: OrchestratorContext, tool_result: dict) -> str:
        if tool_result.get("success"):
            data = tool_result.get("data") or {}
            if isinstance(data, dict) and data.get("reply_text"):
                return str(data["reply_text"])
            return json.dumps(data, ensure_ascii=False, default=str)

        domain = ctx.intent.get("domain") if ctx.intent else None
        if domain == "dutch_tutor":
            return "Ik kon dat woord niet verwerken. Probeer een enkel Nederlands woord zoals 'huis'."
        return f"I couldn't complete that action: {tool_result.get('error', 'unknown error')}"

    def _get_plugin(self, domain_id: str | None) -> DomainPlugin | None:
        if not domain_id:
            return None
        if self.domain_plugins is not None:
            return self.domain_plugins.get(domain_id)
        return get_loaded_plugin(domain_id)

    async def _emit_ingress_event(self, ctx: OrchestratorContext) -> None:
        """Emit a communication ingress event once the message enters orchestration."""
        event = PlatformEvent(
            event_type="communication.message_received",
            event_category="communication",
            domain=ctx.intent.get("domain") if ctx.intent else None,
            correlation_id=ctx.correlation_id,
            payload={
                "message_id": str(ctx.message_id) if ctx.message_id else None,
                "conversation_id": str(ctx.conversation_id) if ctx.conversation_id else None,
                "channel_type": ctx.channel_type,
                "channel_user_id": ctx.channel_user_id,
                "external_chat_id": ctx.external_chat_id,
                "bot_id": ctx.bot_id,
                "target_domain": ctx.target_domain,
                "content_type": str(ctx.content_type),
            },
            source="communication",
        )
        await self.event_bus.publish(event, session=self.session)

    async def _emit_events(self, ctx: OrchestratorContext) -> None:
        """Emit platform events for this interaction."""
        platform_event = PlatformEvent(
            event_type="system.message_processed",
            event_category="system",
            correlation_id=ctx.correlation_id,
            domain=ctx.intent.get("domain") if ctx.intent else None,
            payload={
                "message_id": str(ctx.message_id) if ctx.message_id else None,
                "conversation_id": str(ctx.conversation_id) if ctx.conversation_id else None,
                "channel_type": ctx.channel_type,
                "intent": ctx.intent,
                "response_length": len(ctx.response_text) if ctx.response_text else 0,
                "bot_id": ctx.bot_id,
            },
            source="system",
        )
        await self.event_bus.publish(platform_event, session=self.session)

        if ctx.intent and ctx.intent.get("domain"):
            domain_event = PlatformEvent(
                event_type=f"{ctx.intent['domain']}.message_processed",
                event_category="domain",
                domain=ctx.intent["domain"],
                correlation_id=ctx.correlation_id,
                payload={
                    "message_id": str(ctx.message_id) if ctx.message_id else None,
                    "conversation_id": str(ctx.conversation_id) if ctx.conversation_id else None,
                    "channel_type": ctx.channel_type,
                    "bot_id": ctx.bot_id,
                    "response_length": len(ctx.response_text) if ctx.response_text else 0,
                },
                source="system",
            )
            await self.event_bus.publish(domain_event, session=self.session)
