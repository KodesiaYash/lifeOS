"""
Telegram channel adapter.
"""

import httpx
import structlog

from src.config import settings
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

    def __init__(
        self,
        bot_token: str = "",
        webhook_secret: str = "",
        api_base: str = "",
    ) -> None:
        self.bot_token = bot_token or settings.TELEGRAM_BOT_TOKEN
        self.webhook_secret = webhook_secret or settings.TELEGRAM_WEBHOOK_SECRET
        self.api_base = (api_base or settings.TELEGRAM_API_BASE).rstrip("/")

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
                idempotency_key=f"telegram:{chat.get('id', '')}:{message.get('message_id', '')}",
                raw_payload=raw_payload,
            )
        except (IndexError, KeyError):
            logger.exception("telegram_parse_error")
            return None

    async def send_message(self, message: OutboundMessage) -> DeliveryReceipt:
        """Send a message via Telegram Bot API."""
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is not configured")

        payload: dict[str, object] = {
            "chat_id": message.recipient_channel_id,
            "text": message.text or "",
        }
        if message.reply_to_message_id:
            payload["reply_to_message_id"] = int(message.reply_to_message_id)

        data = await self._post_json("sendMessage", payload)
        result = data.get("result", {})
        channel_message_id = str(result.get("message_id", ""))
        logger.info(
            "telegram_send_success",
            recipient=message.recipient_channel_id,
            channel_message_id=channel_message_id,
        )
        return DeliveryReceipt(
            channel_message_id=channel_message_id,
            status="sent",
        )

    async def set_webhook(self, webhook_url: str, secret_token: str | None = None) -> dict:
        """Register the Telegram webhook for this bot."""
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is not configured")
        payload: dict[str, object] = {
            "url": webhook_url,
            "allowed_updates": ["message"],
        }
        if secret_token:
            payload["secret_token"] = secret_token
        data = await self._post_json("setWebhook", payload)
        logger.info("telegram_webhook_configured", webhook_url=webhook_url)
        return data

    async def _post_json(self, method: str, payload: dict[str, object]) -> dict:
        url = f"{self.api_base}/bot{self.bot_token}/{method}"
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
        if not data.get("ok"):
            raise ValueError(f"Telegram API rejected the request: {data}")
        return data
