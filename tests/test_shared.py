"""
Tests for shared utilities.
"""
from datetime import datetime, timezone

import pytest

from src.shared.crypto import decrypt, encrypt
from src.shared.pagination import PaginatedResult, PaginationParams
from src.shared.time import format_iso, utc_now


class TestCrypto:
    def test_encrypt_decrypt_roundtrip(self):
        plaintext = "my-secret-api-key"
        encrypted = encrypt(plaintext)
        assert encrypted != plaintext.encode()
        decrypted = decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_empty_string(self):
        encrypted = encrypt("")
        assert decrypt(encrypted) == ""

    def test_encrypt_unicode(self):
        plaintext = "héllo wörld 🌍"
        encrypted = encrypt(plaintext)
        assert decrypt(encrypted) == plaintext


class TestTime:
    def test_utc_now_is_timezone_aware(self):
        now = utc_now()
        assert now.tzinfo is not None
        assert now.tzinfo == timezone.utc

    def test_format_iso(self):
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = format_iso(dt)
        assert "2024-01-15" in result
        assert "10:30" in result


class TestPagination:
    def test_pagination_params_defaults(self):
        params = PaginationParams()
        assert params.page == 1
        assert params.size == 50

    def test_pagination_params_offset(self):
        params = PaginationParams(page=3, size=20)
        assert params.offset == 40

    def test_paginated_result(self):
        result = PaginatedResult(
            items=["a", "b", "c"],
            total=100,
            page=2,
            size=3,
        )
        assert result.pages == 34
        assert len(result.items) == 3
