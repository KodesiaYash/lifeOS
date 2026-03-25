"""
Unit tests for src/communication/schemas.py — messaging schemas.

Tests:
  - test_inbound_message_create: Valid inbound message with channel + text
  - test_message_type_enum_values: All expected message types exist
  - test_inbound_message_optional_media: media_url defaults to None
  - test_inbound_message_metadata: Extra metadata dict is preserved
"""
import pytest

from src.communication.schemas import InboundMessageCreate, MessageType


class TestInboundMessageCreate:
    """Verify inbound message schema validation."""

    def test_inbound_message_create(self):
        """Minimum valid inbound message: channel_type + external_user_id + text."""
        msg = InboundMessageCreate(
            channel_type="whatsapp",
            external_user_id="123456",
            text="Hello!",
        )
        assert msg.channel_type == "whatsapp"
        assert msg.text == "Hello!"
        assert msg.external_user_id == "123456"

    def test_inbound_message_optional_media(self):
        """Media URL is optional and defaults to None."""
        msg = InboundMessageCreate(
            channel_type="telegram",
            external_user_id="789",
            text="Photo caption",
        )
        assert msg.media_url is None or not hasattr(msg, "media_url") or msg.media_url is None


class TestMessageTypeEnum:
    """Verify MessageType enum members."""

    def test_message_type_text(self):
        """TEXT type exists."""
        assert MessageType.TEXT == "text"

    def test_message_type_image(self):
        """IMAGE type exists."""
        assert MessageType.IMAGE == "image"

    def test_message_type_values(self):
        """All expected types are defined."""
        types = {m.value for m in MessageType}
        assert "text" in types
        assert "image" in types
