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
    ChannelAccount,
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

    async def get_or_create(self, channel_type: str, display_name: str, config: dict | None = None) -> Channel:
        channel = await self.get_by_type(channel_type)
        if channel is not None:
            return channel

        channel = Channel(
            type=channel_type,
            display_name=display_name,
            config=config or {},
            active=True,
        )
        self.session.add(channel)
        await self.session.flush()
        return channel


class ChannelAccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_ref(self, channel_id: uuid.UUID, account_ref: str) -> ChannelAccount | None:
        result = await self.session.execute(
            select(ChannelAccount).where(
                ChannelAccount.channel_id == channel_id,
                ChannelAccount.account_ref == account_ref,
                ChannelAccount.active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        *,
        channel_id: uuid.UUID,
        account_ref: str,
        display_name: str | None = None,
        credentials_ref: str | None = None,
        config: dict | None = None,
    ) -> ChannelAccount:
        account = await self.get_by_ref(channel_id, account_ref)
        if account is not None:
            return account

        account = ChannelAccount(
            channel_id=channel_id,
            account_ref=account_ref,
            display_name=display_name,
            credentials_ref=credentials_ref,
            config=config or {},
            active=True,
        )
        self.session.add(account)
        await self.session.flush()
        return account


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
        external_chat_id: str | None = None,
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
            if external_chat_id and conversation.external_chat_id != external_chat_id:
                conversation.external_chat_id = external_chat_id
                await self.session.flush()
            return conversation

        conversation = Conversation(
            channel_identity_id=channel_identity_id,
            channel_type=channel_type,
            external_chat_id=external_chat_id,
        )
        self.session.add(conversation)
        await self.session.flush()
        return conversation

    async def get_by_id(self, conversation_id: uuid.UUID) -> Conversation | None:
        result = await self.session.execute(select(Conversation).where(Conversation.id == conversation_id))
        return result.scalar_one_or_none()

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
