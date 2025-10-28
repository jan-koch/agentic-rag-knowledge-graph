"""
Encryption utilities for API key storage.

Uses AES-256-GCM via Fernet for symmetric encryption.
"""

import os
import base64
import logging
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    """Raised when encryption/decryption fails."""
    pass


def get_encryption_key() -> bytes:
    """
    Get or generate the encryption key from environment.

    Returns:
        bytes: The encryption key for Fernet

    Raises:
        EncryptionError: If ENCRYPTION_KEY is not set
    """
    encryption_key = os.getenv("ENCRYPTION_KEY")

    if not encryption_key:
        raise EncryptionError(
            "ENCRYPTION_KEY environment variable not set. "
            "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )

    # If the key is not in the correct format, derive it using PBKDF2
    try:
        # Try to use it directly as a Fernet key
        Fernet(encryption_key.encode())
        return encryption_key.encode()
    except Exception:
        # If it fails, derive a proper Fernet key from the provided string
        logger.info("Deriving Fernet key from ENCRYPTION_KEY")
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'api_key_encryption_salt',  # Static salt for consistency
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
        return key


def encrypt_api_key(plain_key: str) -> str:
    """
    Encrypt an API key.

    Args:
        plain_key: The plain text API key

    Returns:
        str: The encrypted key (base64 encoded)

    Raises:
        EncryptionError: If encryption fails
    """
    try:
        encryption_key = get_encryption_key()
        fernet = Fernet(encryption_key)
        encrypted = fernet.encrypt(plain_key.encode())
        return encrypted.decode()
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise EncryptionError(f"Failed to encrypt API key: {str(e)}")


def decrypt_api_key(encrypted_key: str) -> str:
    """
    Decrypt an API key.

    Args:
        encrypted_key: The encrypted key (base64 encoded)

    Returns:
        str: The plain text API key

    Raises:
        EncryptionError: If decryption fails
    """
    try:
        encryption_key = get_encryption_key()
        fernet = Fernet(encryption_key)
        decrypted = fernet.decrypt(encrypted_key.encode())
        return decrypted.decode()
    except InvalidToken:
        raise EncryptionError("Invalid encryption key or corrupted data")
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise EncryptionError(f"Failed to decrypt API key: {str(e)}")


def test_encryption() -> bool:
    """
    Test encryption/decryption functionality.

    Returns:
        bool: True if test passes
    """
    try:
        test_key = "test_key_12345"
        encrypted = encrypt_api_key(test_key)
        decrypted = decrypt_api_key(encrypted)
        return decrypted == test_key
    except Exception as e:
        logger.error(f"Encryption test failed: {e}")
        return False


if __name__ == "__main__":
    # Test encryption when run directly
    print("Testing encryption...")
    if test_encryption():
        print("✓ Encryption test passed")
    else:
        print("✗ Encryption test failed")
