"""
Unit tests for src/communication/adapters/telegram.py.
"""

import pytest

from src.communication.adapters.telegram import TelegramAdapter
from src.communication.schemas import ChannelType, ContentType, OutboundMessage


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class _FakeAsyncClient:
    calls: list[tuple[str, dict]] = []

    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url: str, json: dict):
        self.calls.append((url, json))
        return _FakeResponse({"ok": True, "result": {"message_id": 123}})


class TestTelegramAdapter:
    @pytest.mark.asyncio
    async def test_normalize_inbound_message(self):
        adapter = TelegramAdapter(bot_token="token", webhook_secret="secret")
        event = await adapter.normalize_inbound(
            {
                "message": {
                    "message_id": 10,
                    "text": "Hallo",
                    "chat": {"id": 555},
                    "from": {"id": 999, "first_name": "Yash"},
                }
            }
        )

        assert event is not None
        assert event.channel_type == ChannelType.TELEGRAM
        assert event.content_type == ContentType.TEXT
        assert event.text == "Hallo"
        assert event.idempotency_key == "telegram:555:10"

    @pytest.mark.asyncio
    async def test_send_message_uses_telegram_api(self, monkeypatch):
        monkeypatch.setattr("src.communication.adapters.telegram.httpx.AsyncClient", _FakeAsyncClient)
        _FakeAsyncClient.calls.clear()
        adapter = TelegramAdapter(bot_token="bot-token", webhook_secret="secret", api_base="https://api.telegram.org")

        receipt = await adapter.send_message(
            OutboundMessage(
                channel_type=ChannelType.TELEGRAM,
                recipient_channel_id="555",
                text="Hoi",
            )
        )

        assert receipt.status == "sent"
        assert receipt.channel_message_id == "123"
        assert _FakeAsyncClient.calls[0][0].endswith("/sendMessage")
        assert _FakeAsyncClient.calls[0][1]["chat_id"] == "555"

    @pytest.mark.asyncio
    async def test_set_webhook_uses_telegram_api(self, monkeypatch):
        monkeypatch.setattr("src.communication.adapters.telegram.httpx.AsyncClient", _FakeAsyncClient)
        _FakeAsyncClient.calls.clear()
        adapter = TelegramAdapter(bot_token="bot-token", webhook_secret="secret", api_base="https://api.telegram.org")

        response = await adapter.set_webhook("https://example.com/telegram", secret_token="secret")

        assert response["ok"] is True
        assert _FakeAsyncClient.calls[0][0].endswith("/setWebhook")
        assert _FakeAsyncClient.calls[0][1]["url"] == "https://example.com/telegram"
        assert _FakeAsyncClient.calls[0][1]["secret_token"] == "secret"
