"""
Unit tests for src/shared/crypto.py — encryption utilities.

Tests:
  - test_encrypt_decrypt_roundtrip: Encrypting then decrypting returns original plaintext
  - test_encrypt_empty_string: Edge case — empty string survives roundtrip
  - test_encrypt_unicode: Non-ASCII characters (accents, emoji) survive roundtrip
  - test_encrypt_produces_different_ciphertext: Same plaintext encrypted twice produces different bytes (Fernet uses random IV)
  - test_decrypt_invalid_token_raises: Corrupted ciphertext raises an error
  - test_encrypt_long_string: Large payloads (API responses, JSON blobs) survive roundtrip
"""
import pytest

from src.shared.crypto import decrypt, encrypt


class TestEncrypt:
    """Verify Fernet symmetric encryption correctness."""

    def test_encrypt_decrypt_roundtrip(self):
        """Standard plaintext survives encrypt → decrypt."""
        plaintext = "my-secret-api-key"
        encrypted = encrypt(plaintext)
        assert encrypted != plaintext.encode()
        assert decrypt(encrypted) == plaintext

    def test_encrypt_empty_string(self):
        """Empty string is a valid input and must roundtrip."""
        encrypted = encrypt("")
        assert decrypt(encrypted) == ""

    def test_encrypt_unicode(self):
        """Non-ASCII (accents, emoji) must survive roundtrip — UTF-8 encoding."""
        plaintext = "héllo wörld 🌍"
        encrypted = encrypt(plaintext)
        assert decrypt(encrypted) == plaintext

    def test_encrypt_produces_different_ciphertext(self):
        """Fernet uses a random IV, so two encryptions of the same text differ."""
        plaintext = "same-input"
        a = encrypt(plaintext)
        b = encrypt(plaintext)
        assert a != b  # different ciphertext
        assert decrypt(a) == decrypt(b) == plaintext  # same plaintext

    def test_decrypt_invalid_token_raises(self):
        """Corrupted ciphertext must raise, never silently return garbage."""
        with pytest.raises(Exception):
            decrypt(b"not-a-valid-fernet-token")

    def test_encrypt_long_string(self):
        """Large payloads (e.g. OAuth token JSON) must roundtrip."""
        plaintext = "x" * 10_000
        assert decrypt(encrypt(plaintext)) == plaintext
