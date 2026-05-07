from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import get_settings


def _get_key() -> bytes:
    raw = base64.b64decode(get_settings().teller_token_enc_key)
    if len(raw) != 32:
        raise ValueError("TELLER_TOKEN_ENC_KEY must decode to exactly 32 bytes")
    return raw


def encrypt(plaintext: str) -> str:
    """Encrypt with AES-256-GCM. Returns base64(nonce || ciphertext_with_tag)."""
    aes = AESGCM(_get_key())
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ct).decode("ascii")


def decrypt(blob: str) -> str:
    raw = base64.b64decode(blob)
    nonce, ct = raw[:12], raw[12:]
    aes = AESGCM(_get_key())
    return aes.decrypt(nonce, ct, None).decode("utf-8")
