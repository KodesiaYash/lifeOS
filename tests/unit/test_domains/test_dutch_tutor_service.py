"""Unit tests for the promoted Dutch tutor domain service."""

from __future__ import annotations

import pytest

from src.domains.dutch_tutor.service import DutchTutorService


@pytest.mark.req("REQ-DUTCH-001")
@pytest.mark.scenario("SCN-REQ-DUTCH-001-01")
def test_translate_roundtrip_known_dutch_word():
    result = DutchTutorService.translate_roundtrip("huis")

    assert result.known_word is True
    assert result.detected_language == "dutch"
    assert result.english_word == "house"
    assert result.back_to_dutch == "huis"
    assert result.reply_text == "Nederlands: huis\nEnglish: house\nBack to Dutch: huis"


@pytest.mark.req("REQ-DUTCH-001")
@pytest.mark.scenario("SCN-REQ-DUTCH-001-02")
def test_translate_roundtrip_known_english_word():
    result = DutchTutorService.translate_roundtrip("book")

    assert result.known_word is True
    assert result.detected_language == "english"
    assert result.dutch_word == "boek"
    assert result.english_word == "book"
    assert result.back_to_dutch == "boek"


@pytest.mark.req("REQ-DUTCH-001")
@pytest.mark.scenario("SCN-REQ-DUTCH-001-03")
@pytest.mark.asyncio
async def test_capture_memory_splits_general_and_domain_namespaces(mock_db_session, monkeypatch):
    captured_calls: list[dict] = []

    class _FakeMemoryService:
        def __init__(self, session) -> None:
            self.session = session

        @staticmethod
        def normalize_namespace(namespace: str | None) -> str:
            return (namespace or "general").strip() or "general"

        async def upsert_fact(self, **kwargs):
            captured_calls.append(kwargs)
            return None

    monkeypatch.setattr("src.domains.dutch_tutor.service.MemoryService", _FakeMemoryService)

    await DutchTutorService.capture_memory(
        mock_db_session,
        user_message="My native language is English and my Dutch level is A2",
        user_name="Yash",
    )

    assert {call["namespace"] for call in captured_calls} == {"general", "dutch_tutor"}
    assert any(call["key"] == "profile.display_name" and call["namespace"] == "general" for call in captured_calls)
    assert any(call["key"] == "profile.native_language" and call["namespace"] == "general" for call in captured_calls)
    assert any(call["key"] == "dutch.cefr_level" and call["namespace"] == "dutch_tutor" for call in captured_calls)
