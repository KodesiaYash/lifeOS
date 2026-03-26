"""
Abstract base class for channel adapters.
"""

from abc import ABC, abstractmethod

from src.communication.schemas import DeliveryReceipt, NormalizedInboundEvent, OutboundMessage


class ChannelAdapter(ABC):
    """
    Base interface for communication channel adapters.
    Each channel (WhatsApp, Telegram, REST API) implements this interface.
    """

    @abstractmethod
    async def normalize_inbound(self, raw_payload: dict) -> NormalizedInboundEvent | None:
        """
        Parse a raw webhook payload into a NormalizedInboundEvent.
        Returns None if the payload is not a user message (e.g., status update).
        """
        ...

    @abstractmethod
    async def send_message(self, message: OutboundMessage) -> DeliveryReceipt:
        """Send an outbound message and return a delivery receipt."""
        ...

    @abstractmethod
    async def verify_webhook(self, headers: dict, body: bytes) -> bool:
        """Verify the authenticity of an incoming webhook request."""
        ...

    @abstractmethod
    def channel_type(self) -> str:
        """Return the channel type identifier (e.g., 'whatsapp')."""
        ...
