"""
REST API channel adapter.
Pass-through adapter for direct API access — no external webhook needed.
"""

import uuid

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


class RestApiAdapter(ChannelAdapter):
    """REST API adapter — messages come directly from authenticated API calls."""

    def channel_type(self) -> str:
        return ChannelType.REST_API

    async def verify_webhook(self, headers: dict, body: bytes) -> bool:
        """REST API requests are verified via JWT auth, not webhook signatures."""
        return True

    async def normalize_inbound(self, raw_payload: dict) -> NormalizedInboundEvent | None:
        """Normalize a REST API message payload."""
        text = raw_payload.get("text")
        user_id = raw_payload.get("user_id", "")

        return NormalizedInboundEvent(
            channel_type=ChannelType.REST_API,
            channel_user_id=str(user_id),
            content_type=ContentType(raw_payload.get("content_type", "text")),
            text=text,
            media_url=raw_payload.get("media_url"),
            media_mime_type=raw_payload.get("media_mime_type"),
            idempotency_key=raw_payload.get("idempotency_key", f"rest_{uuid.uuid4()}"),
            raw_payload=raw_payload,
        )

    async def send_message(self, message: OutboundMessage) -> DeliveryReceipt:
        """
        REST API adapter doesn't actively push messages.
        The response is returned inline in the API response.
        """
        return DeliveryReceipt(
            channel_message_id=f"rest_{uuid.uuid4()}",
            status="delivered",
        )
