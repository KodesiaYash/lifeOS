"""
Telegram channel adapter.
Stub implementation — webhook parsing and message sending scaffolded.
"""

import structlog

from src.communication.adapters.base import ChannelAdapter
from src.communication.schemas import (
    ChannelType,
    ContentType,
    DeliveryReceipt,
    NormalizedInboundEvent,
    OutboundMessage,
)

logger = structlog.get_logger()


class TelegramAdapter(ChannelAdapter):
    """Telegram Bot API adapter (webhook mode)."""

    def __init__(self, bot_token: str = "", webhook_secret: str = "") -> None:
        self.bot_token = bot_token
        self.webhook_secret = webhook_secret

    def channel_type(self) -> str:
        return ChannelType.TELEGRAM

    async def verify_webhook(self, headers: dict, body: bytes) -> bool:
        """Verify Telegram webhook secret token."""
        token = headers.get("x-telegram-bot-api-secret-token", "")
        if not self.webhook_secret:
            return True  # No secret configured — accept all
        return token == self.webhook_secret

    async def normalize_inbound(self, raw_payload: dict) -> NormalizedInboundEvent | None:
        """Parse a Telegram webhook update into a NormalizedInboundEvent."""
        try:
            message = raw_payload.get("message")
            if not message:
                return None

            chat = message.get("chat", {})
            from_user = message.get("from", {})

            text = message.get("text")
            content_type = ContentType.TEXT
            media_url = None

            if "photo" in message:
                content_type = ContentType.IMAGE
                photos = message["photo"]
                media_url = photos[-1].get("file_id") if photos else None
            elif "document" in message:
                content_type = ContentType.DOCUMENT
                media_url = message["document"].get("file_id")
            elif "voice" in message:
                content_type = ContentType.AUDIO
                media_url = message["voice"].get("file_id")

            return NormalizedInboundEvent(
                channel_type=ChannelType.TELEGRAM,
                channel_user_id=str(from_user.get("id", "")),
                external_chat_id=str(chat.get("id", "")),
                content_type=content_type,
                text=text,
                media_url=media_url,
                idempotency_key=f"tg_{message.get('message_id', '')}_{chat.get('id', '')}",
                raw_payload=raw_payload,
            )
        except (IndexError, KeyError):
            logger.exception("telegram_parse_error")
            return None

    async def send_message(self, message: OutboundMessage) -> DeliveryReceipt:
        """
        Send a message via Telegram Bot API.
        TODO: Implement actual HTTP call to Telegram API.
        """
        logger.info(
            "telegram_send_stub",
            recipient=message.recipient_channel_id,
            text_preview=message.text[:50] if message.text else None,
        )
        return DeliveryReceipt(
            channel_message_id=f"tg_stub_{message.recipient_channel_id}",
            status="sent",
        )
