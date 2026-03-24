"""
WhatsApp channel adapter (Meta Cloud API).
Stub implementation — webhook parsing and message sending scaffolded.
"""
import hashlib
import hmac

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


class WhatsAppAdapter(ChannelAdapter):
    """WhatsApp Business Cloud API adapter."""

    def __init__(self, phone_number_id: str = "", access_token: str = "", app_secret: str = "") -> None:
        self.phone_number_id = phone_number_id
        self.access_token = access_token
        self.app_secret = app_secret

    def channel_type(self) -> str:
        return ChannelType.WHATSAPP

    async def verify_webhook(self, headers: dict, body: bytes) -> bool:
        """Verify Meta's X-Hub-Signature-256 header."""
        signature = headers.get("x-hub-signature-256", "")
        if not signature or not self.app_secret:
            return False
        expected = "sha256=" + hmac.new(
            self.app_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(signature, expected)

    async def normalize_inbound(self, raw_payload: dict) -> NormalizedInboundEvent | None:
        """
        Parse a WhatsApp Cloud API webhook payload.
        Returns None for non-message events (status updates, etc.).
        """
        try:
            entry = raw_payload.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            messages = value.get("messages", [])

            if not messages:
                return None

            msg = messages[0]
            contact = value.get("contacts", [{}])[0]

            text = None
            content_type = ContentType.TEXT
            media_url = None

            if msg.get("type") == "text":
                text = msg.get("text", {}).get("body")
            elif msg.get("type") in ("image", "audio", "video", "document"):
                content_type = ContentType(msg["type"])
                media_url = msg.get(msg["type"], {}).get("id")  # Media ID, needs download
            else:
                text = str(msg)

            return NormalizedInboundEvent(
                channel_type=ChannelType.WHATSAPP,
                channel_user_id=msg.get("from", ""),
                content_type=content_type,
                text=text,
                media_url=media_url,
                idempotency_key=msg.get("id", ""),
                raw_payload=raw_payload,
            )
        except (IndexError, KeyError):
            logger.exception("whatsapp_parse_error")
            return None

    async def send_message(self, message: OutboundMessage) -> DeliveryReceipt:
        """
        Send a message via WhatsApp Cloud API.
        TODO: Implement actual HTTP call to Meta API.
        """
        logger.info(
            "whatsapp_send_stub",
            recipient=message.recipient_channel_id,
            text_preview=message.text[:50] if message.text else None,
        )
        # Stub — return a fake receipt
        return DeliveryReceipt(
            channel_message_id=f"wamid_stub_{message.recipient_channel_id}",
            status="sent",
        )
