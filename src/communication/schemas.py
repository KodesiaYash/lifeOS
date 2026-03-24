"""
Pydantic schemas for the communication layer.
"""
import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ChannelType(StrEnum):
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    REST_API = "rest_api"
    WEB_APP = "web_app"
    EMAIL = "email"
    SLACK = "slack"
    VOICE = "voice"


class MessageDirection(StrEnum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class ContentType(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    LOCATION = "location"
    CONTACT = "contact"
    INTERACTIVE = "interactive"
    SYSTEM = "system"


class NormalizedInboundEvent(BaseModel):
    """Canonical inbound message from any channel."""
    channel_type: ChannelType
    channel_account_id: uuid.UUID | None = None
    channel_user_id: str                       # External user ID on the channel
    external_chat_id: str | None = None        # Channel's chat/thread ID
    content_type: ContentType = ContentType.TEXT
    text: str | None = None
    media_url: str | None = None
    media_mime_type: str | None = None
    idempotency_key: str                       # Channel-unique message ID
    raw_payload: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class OutboundMessage(BaseModel):
    """Message to send via a channel adapter."""
    channel_type: ChannelType
    channel_account_id: uuid.UUID | None = None
    recipient_channel_id: str                  # External user ID on the channel
    content_type: ContentType = ContentType.TEXT
    text: str | None = None
    media_url: str | None = None
    media_mime_type: str | None = None
    reply_to_message_id: str | None = None
    metadata: dict = Field(default_factory=dict)


class DeliveryReceipt(BaseModel):
    """Delivery status from a channel."""
    channel_message_id: str
    status: str                                # "sent", "delivered", "read", "failed"
    error_code: str | None = None
    error_message: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    channel_type: str
    platform_user_id: uuid.UUID | None
    started_at: datetime
    last_message_at: datetime | None
    message_count: int

    model_config = {"from_attributes": True}


class MessageRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    conversation_id: uuid.UUID
    direction: str
    content_type: str
    text: str | None
    channel_message_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
