"""
Startup bootstrap for communication channels and channel accounts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.communication.repository import ChannelAccountRepository, ChannelRepository
from src.communication.schemas import ChannelType
from src.config import settings

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession


class CommunicationBootstrap:
    """Ensures default channels and channel accounts exist."""

    def __init__(self, session: AsyncSession) -> None:
        self.channels = ChannelRepository(session)
        self.accounts = ChannelAccountRepository(session)

    async def ensure_default_accounts(self) -> dict[str, uuid.UUID]:
        """Create the minimum channels needed for the current routed domains."""
        bindings: dict[str, uuid.UUID] = {}

        rest_channel = await self.channels.get_or_create(
            channel_type=ChannelType.REST_API,
            display_name="REST API",
        )
        rest_account = await self.accounts.get_or_create(
            channel_id=rest_channel.id,
            account_ref="rest_api:default",
            display_name="REST API Default",
        )
        bindings[ChannelType.REST_API] = rest_account.id

        if settings.DUTCH_TUTOR_ENABLED:
            telegram_channel = await self.channels.get_or_create(
                channel_type=ChannelType.TELEGRAM,
                display_name="Telegram",
            )
            telegram_account = await self.accounts.get_or_create(
                channel_id=telegram_channel.id,
                account_ref=f"telegram:{settings.DUTCH_TUTOR_BOT_ID}",
                display_name="Dutch Tutor Telegram",
                credentials_ref="env:TELEGRAM_BOT_TOKEN",
            )
            bindings[ChannelType.TELEGRAM] = telegram_account.id

        return bindings
