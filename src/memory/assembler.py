"""
Memory packet assembly: gather relevant context from all memory layers
and assemble into a bounded MemoryPacket for LLM calls.

Single-user mode: No tenant_id or user_id needed.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.memory.repository import ConversationSummaryRepository, MemoryFactRepository, SemanticMemoryRepository
from src.memory.schemas import MemoryFactRead, MemoryPacket, ScopedMemoryPacket, SemanticMemoryRead
from src.memory.short_term import ShortTermMemory

logger = structlog.get_logger()

# Rough token estimates per item
TOKENS_PER_FACT = 30
TOKENS_PER_SEMANTIC = 80
TOKENS_PER_SUMMARY = 100
DEFAULT_TOKEN_BUDGET = 3000


class MemoryAssembler:
    """
    Assembles a MemoryPacket from all memory layers within a token budget.
    Priority order: session context > active facts > semantic memories > conversation summaries.
    """

    def __init__(
        self,
        session: AsyncSession,
        short_term: ShortTermMemory | None = None,
    ) -> None:
        self.session = session
        self.short_term = short_term or ShortTermMemory()
        self.facts_repo = MemoryFactRepository(session)
        self.semantic_repo = SemanticMemoryRepository(session)
        self.summaries_repo = ConversationSummaryRepository(session)

    async def assemble(
        self,
        query_embedding: list[float] | None = None,
        domain: str | None = None,
        domains: list[str] | None = None,
        token_budget: int = DEFAULT_TOKEN_BUDGET,
        session_id: str | None = None,
    ) -> MemoryPacket:
        """
        Assemble a memory packet with relevant context from all layers.
        Respects the token budget to avoid overflowing the LLM context window.
        """
        packet = MemoryPacket()
        remaining = token_budget

        # 1. Session context (short-term memory)
        session_state = await self.short_term.get_session(session_id)
        if session_state:
            packet.session_context = {
                k: v
                for k, v in session_state.items()
                if k != "message_history"  # Message history is handled separately
            }
            remaining -= 200  # Estimate for session context

        # 2. Structured facts (highest priority — user preferences, goals, etc.)
        facts = await self.facts_repo.list_all_active(domain=domain, domains=domains)
        for fact in facts:
            if remaining < TOKENS_PER_FACT:
                break
            packet.user_facts.append(MemoryFactRead.model_validate(fact))
            remaining -= TOKENS_PER_FACT

        # 3. Semantic memories (if we have a query embedding)
        if query_embedding and remaining > TOKENS_PER_SEMANTIC:
            max_semantic = min(10, remaining // TOKENS_PER_SEMANTIC)
            semantic_results = await self.semantic_repo.search_by_embedding(
                embedding=query_embedding,
                limit=max_semantic,
                domain=domain,
                domains=domains,
            )
            for mem in semantic_results:
                if remaining < TOKENS_PER_SEMANTIC:
                    break
                packet.semantic_memories.append(SemanticMemoryRead.model_validate(mem))
                remaining -= TOKENS_PER_SEMANTIC

        # 4. Recent conversation summaries
        if remaining > TOKENS_PER_SUMMARY:
            max_summaries = min(5, remaining // TOKENS_PER_SUMMARY)
            summaries = await self.summaries_repo.list_recent(limit=max_summaries, domains=domains)
            for s in summaries:
                if remaining < TOKENS_PER_SUMMARY:
                    break
                packet.recent_summaries.append(s.summary)
                remaining -= TOKENS_PER_SUMMARY

        packet.total_tokens_estimate = token_budget - remaining
        logger.info(
            "memory_packet_assembled",
            facts=len(packet.user_facts),
            semantic=len(packet.semantic_memories),
            summaries=len(packet.recent_summaries),
            tokens_used=packet.total_tokens_estimate,
        )
        return packet

    async def assemble_scoped(
        self,
        namespace: str,
        general_namespace: str,
        query_embedding: list[float] | None = None,
        token_budget: int = DEFAULT_TOKEN_BUDGET,
        session_id: str | None = None,
    ) -> ScopedMemoryPacket:
        """
        Assemble context for a routed domain, splitting general memory from domain-scoped memory.
        """
        packet = await self.assemble(
            query_embedding=query_embedding,
            domains=[general_namespace, namespace],
            token_budget=token_budget,
            session_id=session_id,
        )
        return ScopedMemoryPacket(
            namespace=namespace,
            general_namespace=general_namespace,
            general_facts=[fact for fact in packet.user_facts if fact.domain == general_namespace],
            scoped_facts=[fact for fact in packet.user_facts if fact.domain == namespace],
            general_semantic_memories=[
                memory for memory in packet.semantic_memories if memory.source_domain == general_namespace
            ],
            scoped_semantic_memories=[
                memory for memory in packet.semantic_memories if memory.source_domain == namespace
            ],
            recent_summaries=packet.recent_summaries,
            session_context=packet.session_context,
            total_tokens_estimate=packet.total_tokens_estimate,
        )
