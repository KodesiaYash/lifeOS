"""
Communication service: conversation management, identity resolution, idempotency.

Single-user mode: No tenant_id needed.
"""

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.communication.models import Message
from src.communication.repository import (
    ChannelIdentityRepository,
    ConversationRepository,
    MessageRepository,
)
from src.communication.schemas import NormalizedInboundEvent

logger = structlog.get_logger()


class CommunicationService:
    """Orchestrates inbound message processing."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.identities = ChannelIdentityRepository(session)
        self.conversations = ConversationRepository(session)
        self.messages = MessageRepository(session)

    async def process_inbound(
        self,
        channel_account_id: uuid.UUID,
        event: NormalizedInboundEvent,
    ) -> Message | None:
        """
        Process a normalized inbound event:
        1. Dedup check (idempotency)
        2. Resolve or create channel identity
        3. Find or create conversation
        4. Persist message
        5. Return the stored message (or None if duplicate)
        """
        # 1. Dedup check
        if await self.messages.exists_by_idempotency_key(event.idempotency_key):
            logger.info("duplicate_message_skipped", idempotency_key=event.idempotency_key)
            return None

        # 2. Resolve channel identity
        identity = await self.identities.get_or_create(
            channel_account_id=channel_account_id,
            external_user_id=event.channel_user_id,
        )

        # 3. Find or create conversation
        conversation = await self.conversations.get_or_create(
            channel_identity_id=identity.id,
            channel_type=event.channel_type,
            external_chat_id=event.external_chat_id,
        )

        # 4. Persist message
        message = Message(
            conversation_id=conversation.id,
            direction="inbound",
            content_type=event.content_type,
            body=event.text,
            media_ref=event.media_url,
            media_mime_type=event.media_mime_type,
            idempotency_key=event.idempotency_key,
            metadata_=event.raw_payload,
        )
        message = await self.messages.create(message)

        # 5. Update conversation stats
        await self.conversations.increment_message_count(conversation.id)

        logger.info(
            "inbound_message_processed",
            message_id=str(message.id),
            conversation_id=str(conversation.id),
            channel_type=event.channel_type,
        )

        return message

    async def store_outbound(
        self,
        conversation_id: uuid.UUID,
        text: str,
        channel_message_id: str | None = None,
        correlation_id: uuid.UUID | None = None,
    ) -> Message:
        """Store an outbound message after it's been sent."""
        message = Message(
            conversation_id=conversation_id,
            direction="outbound",
            content_type="text",
            body=text,
            channel_message_id=channel_message_id,
            idempotency_key=f"out-{uuid.uuid4()}",
            correlation_id=correlation_id,
        )
        message = await self.messages.create(message)
        await self.conversations.increment_message_count(conversation_id)
        return message
