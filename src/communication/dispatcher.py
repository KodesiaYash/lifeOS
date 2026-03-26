"""
Outbound message dispatch with retry logic.
Routes messages to the appropriate channel adapter.
"""

import structlog

from src.communication.adapters.base import ChannelAdapter
from src.communication.schemas import DeliveryReceipt, OutboundMessage

logger = structlog.get_logger()

# Registry of channel adapters, populated at startup
_adapters: dict[str, ChannelAdapter] = {}


def register_adapter(channel_type: str, adapter: ChannelAdapter) -> None:
    """Register a channel adapter for a given channel type."""
    _adapters[channel_type] = adapter
    logger.info("channel_adapter_registered", channel_type=channel_type)


def get_adapter(channel_type: str) -> ChannelAdapter | None:
    """Get the registered adapter for a channel type."""
    return _adapters.get(channel_type)


async def dispatch_message(
    message: OutboundMessage,
    max_retries: int = 3,
) -> DeliveryReceipt:
    """
    Dispatch an outbound message via the appropriate channel adapter.
    Retries on transient failures.
    """
    adapter = get_adapter(message.channel_type)
    if adapter is None:
        logger.error("no_adapter_for_channel", channel_type=message.channel_type)
        return DeliveryReceipt(
            channel_message_id="",
            status="failed",
            error_code="NO_ADAPTER",
            error_message=f"No adapter registered for channel: {message.channel_type}",
        )

    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            receipt = await adapter.send_message(message)
            logger.info(
                "message_dispatched",
                channel_type=message.channel_type,
                status=receipt.status,
                attempt=attempt,
            )
            return receipt
        except Exception as e:
            last_error = e
            logger.warning(
                "dispatch_retry",
                channel_type=message.channel_type,
                attempt=attempt,
                error=str(e),
            )

    return DeliveryReceipt(
        channel_message_id="",
        status="failed",
        error_code="MAX_RETRIES",
        error_message=f"Failed after {max_retries} attempts: {last_error}",
    )
