"""
Database access layer for communication entities.

Single-user mode: No tenant_id filtering.
"""

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.communication.models import (
    Channel,
    ChannelIdentity,
    Conversation,
    Message,
)


class ChannelRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_type(self, channel_type: str) -> Channel | None:
        result = await self.session.execute(
            select(Channel).where(Channel.type == channel_type, Channel.active.is_(True))
        )
        return result.scalar_one_or_none()


class ChannelIdentityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def resolve(self, channel_account_id: uuid.UUID, external_user_id: str) -> ChannelIdentity | None:
        result = await self.session.execute(
            select(ChannelIdentity).where(
                ChannelIdentity.channel_account_id == channel_account_id,
                ChannelIdentity.external_user_id == external_user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        channel_account_id: uuid.UUID,
        external_user_id: str,
        display_name: str | None = None,
    ) -> ChannelIdentity:
        identity = await self.resolve(channel_account_id, external_user_id)
        if identity is not None:
            identity.last_seen_at = datetime.utcnow()
            await self.session.flush()
            return identity

        identity = ChannelIdentity(
            channel_account_id=channel_account_id,
            external_user_id=external_user_id,
            display_name=display_name,
        )
        self.session.add(identity)
        await self.session.flush()
        return identity


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create(
        self,
        channel_identity_id: uuid.UUID,
        channel_type: str,
    ) -> Conversation:
        result = await self.session.execute(
            select(Conversation)
            .where(
                Conversation.channel_identity_id == channel_identity_id,
            )
            .order_by(Conversation.started_at.desc())
            .limit(1)
        )
        conversation = result.scalar_one_or_none()
        if conversation is not None:
            return conversation

        conversation = Conversation(
            channel_identity_id=channel_identity_id,
            channel_type=channel_type,
        )
        self.session.add(conversation)
        await self.session.flush()
        return conversation

    async def increment_message_count(self, conversation_id: uuid.UUID) -> None:
        await self.session.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(
                message_count=Conversation.message_count + 1,
                last_message_at=datetime.utcnow(),
            )
        )


class MessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, message: Message) -> Message:
        self.session.add(message)
        await self.session.flush()
        return message

    async def exists_by_idempotency_key(self, idempotency_key: str) -> bool:
        result = await self.session.execute(
            select(Message.id)
            .where(
                Message.idempotency_key == idempotency_key,
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def list_by_conversation(self, conversation_id: uuid.UUID, limit: int = 50, offset: int = 0) -> list[Message]:
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
