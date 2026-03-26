"""
Background memory consolidation jobs.
Converts ephemeral session data into long-term memories.

Single-user mode: No tenant_id or user_id needed.
"""
import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.memory.models import ConversationSummary, SemanticMemory as SemanticMemoryModel
from src.memory.repository import ConversationSummaryRepository, SemanticMemoryRepository
from src.memory.short_term import ShortTermMemory

logger = structlog.get_logger()


class MemoryConsolidator:
    """
    Background service that consolidates short-term memory into long-term storage.

    Jobs:
    1. Summarize completed conversation sessions → ConversationSummary
    2. Extract patterns from accumulated facts → SemanticMemory
    3. Merge/deduplicate similar semantic memories
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.short_term = ShortTermMemory()
        self.semantic_repo = SemanticMemoryRepository(session)
        self.summary_repo = ConversationSummaryRepository(session)

    async def summarize_session(
        self,
        conversation_id: uuid.UUID | None = None,
        session_id: str | None = None,
    ) -> ConversationSummary | None:
        """
        Summarize a conversation session and store as a ConversationSummary.
        Called when a session times out or is explicitly ended.

        TODO: Implement LLM-based summarization.
        """
        message_history = await self.short_term.get_message_history(session_id)
        if not message_history:
            return None

        # Placeholder — will use LLM to generate summary
        turn_count = len(message_history)
        summary_text = f"Conversation with {turn_count} turns. Topics discussed: [pending LLM summarization]"

        summary = ConversationSummary(
            conversation_id=conversation_id,
            session_id=session_id,
            summary=summary_text,
            key_topics=[],
            domains_involved=[],
            turn_count=turn_count,
            embedding=None,  # Will be computed after LLM summarization
        )
        summary = await self.summary_repo.create(summary)

        logger.info(
            "session_summarized",
            summary_id=str(summary.id),
            turn_count=turn_count,
        )
        return summary

    async def extract_patterns(self) -> list[SemanticMemoryModel]:
        """
        Analyze accumulated facts and summaries to extract behavioral patterns.

        TODO: Implement pattern extraction via LLM.
        Examples:
        - "User tends to log meals at 8am, 1pm, and 7pm"
        - "User exercises more on weekdays"
        - "User prefers concise responses"
        """
        logger.info("pattern_extraction_stub")
        return []

    async def deduplicate_memories(self) -> int:
        """
        Find and merge semantically similar memories.

        TODO: Implement deduplication via embedding similarity.
        """
        logger.info("memory_dedup_stub")
        return 0
