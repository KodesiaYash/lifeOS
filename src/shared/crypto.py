"""
AES-256 encryption/decryption helpers for sensitive data (connector credentials, etc.).
"""
import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from src.config import settings


def _derive_key(key_material: str) -> bytes:
    """Derive a Fernet-compatible key from the configured encryption key."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"ai-life-os-salt",  # Static salt — key material provides entropy
        iterations=100_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(key_material.encode()))


def _get_fernet() -> Fernet:
    return Fernet(_derive_key(settings.ENCRYPTION_KEY))


def encrypt(plaintext: str) -> bytes:
    """Encrypt a string and return encrypted bytes."""
    return _get_fernet().encrypt(plaintext.encode())


def decrypt(ciphertext: bytes) -> str:
    """Decrypt bytes back to a string."""
    return _get_fernet().decrypt(ciphertext).decode()


def generate_encryption_key() -> str:
    """Generate a random encryption key suitable for ENCRYPTION_KEY env var."""
    return base64.urlsafe_b64encode(os.urandom(32)).decode()
