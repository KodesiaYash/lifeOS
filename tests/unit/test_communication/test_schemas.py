"""Unit tests for src/communication/schemas.py — messaging schemas.

Tests:
  - test_normalized_inbound_event: Valid inbound event with channel + text
  - test_content_type_enum_values: All expected content types exist
  - test_channel_type_enum_values: All expected channel types exist
  - test_outbound_message: Valid outbound message schema
"""

from src.communication.schemas import (
    ChannelType,
    ContentType,
    NormalizedInboundEvent,
)


class TestNormalizedInboundEvent:
    """Verify normalized inbound event schema validation."""

    def test_inbound_event_valid(self):
        """Minimum valid inbound event: channel_type + channel_user_id + idempotency_key."""
        event = NormalizedInboundEvent(
            channel_type=ChannelType.WHATSAPP,
            channel_user_id="123456",
            text="Hello!",
            idempotency_key="msg_123",
        )
        assert event.channel_type == ChannelType.WHATSAPP
        assert event.text == "Hello!"
        assert event.channel_user_id == "123456"

    def test_inbound_event_optional_media(self):
        """Media URL is optional and defaults to None."""
        event = NormalizedInboundEvent(
            channel_type=ChannelType.TELEGRAM,
            channel_user_id="789",
            text="Photo caption",
            idempotency_key="msg_456",
        )
        assert event.media_url is None

    def test_inbound_event_default_content_type(self):
        """Default content type is TEXT."""
        event = NormalizedInboundEvent(
            channel_type=ChannelType.REST_API,
            channel_user_id="user1",
            idempotency_key="msg_789",
        )
        assert event.content_type == ContentType.TEXT


class TestContentTypeEnum:
    """Verify ContentType enum members."""

    def test_content_type_text(self):
        """TEXT type exists."""
        assert ContentType.TEXT == "text"

    def test_content_type_image(self):
        """IMAGE type exists."""
        assert ContentType.IMAGE == "image"

    def test_content_type_values(self):
        """All expected types are defined."""
        types = {m.value for m in ContentType}
        assert "text" in types
        assert "image" in types
        assert "audio" in types
        assert "video" in types


class TestChannelTypeEnum:
    """Verify ChannelType enum members."""

    def test_channel_type_whatsapp(self):
        """WHATSAPP type exists."""
        assert ChannelType.WHATSAPP == "whatsapp"

    def test_channel_type_telegram(self):
        """TELEGRAM type exists."""
        assert ChannelType.TELEGRAM == "telegram"

    def test_channel_type_rest_api(self):
        """REST_API type exists."""
        assert ChannelType.REST_API == "rest_api"
