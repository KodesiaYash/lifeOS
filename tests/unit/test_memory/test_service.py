"""
Unit tests for src/memory/service.py.

Tests:
  - test_normalize_namespace_defaults_to_general: Empty namespace becomes general
  - test_upsert_fact_uses_namespace_as_domain: Structured fact writes preserve namespace
  - test_retrieve_scoped_context_passes_embedding_and_namespaces: Scoped retrieval uses shared + domain namespaces
"""

from unittest.mock import AsyncMock

import pytest

from src.memory.schemas import ScopedMemoryPacket
from src.memory.service import GENERAL_MEMORY_NAMESPACE, MemoryService


class TestMemoryService:
    def test_normalize_namespace_defaults_to_general(self, mock_db_session):
        service = MemoryService(mock_db_session)
        assert service.normalize_namespace(None) == GENERAL_MEMORY_NAMESPACE
        assert service.normalize_namespace("") == GENERAL_MEMORY_NAMESPACE

    @pytest.mark.asyncio
    async def test_upsert_fact_uses_namespace_as_domain(self, mock_db_session):
        service = MemoryService(mock_db_session)
        service.structured.remember = AsyncMock(return_value="ok")

        await service.upsert_fact(
            namespace="dutch_tutor",
            category="proficiency",
            key="dutch.cefr_level",
            value="A2",
        )

        create_model = service.structured.remember.await_args.args[0]
        assert create_model.domain == "dutch_tutor"
        assert create_model.key == "dutch.cefr_level"

    @pytest.mark.asyncio
    async def test_retrieve_scoped_context_passes_embedding_and_namespaces(self, mock_db_session):
        service = MemoryService(mock_db_session)
        service.embedding_service.embed_text = AsyncMock(return_value=[0.1, 0.2, 0.3])
        service.assembler.assemble_scoped = AsyncMock(
            return_value=ScopedMemoryPacket(namespace="dutch_tutor", total_tokens_estimate=42)
        )

        packet = await service.retrieve_scoped_context(
            namespace="dutch_tutor",
            query="help me practice grammar",
            session_id="conv-1",
        )

        assert packet.namespace == "dutch_tutor"
        service.assembler.assemble_scoped.assert_awaited_once()
        kwargs = service.assembler.assemble_scoped.await_args.kwargs
        assert kwargs["namespace"] == "dutch_tutor"
        assert kwargs["general_namespace"] == GENERAL_MEMORY_NAMESPACE
        assert kwargs["session_id"] == "conv-1"
