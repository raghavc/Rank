from __future__ import annotations

import base64
import binascii
import hashlib
from typing import TYPE_CHECKING

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

if TYPE_CHECKING:
    pass


def load_ed25519_public_key_from_pem(pem: str) -> Ed25519PublicKey:
    pem = pem.strip()
    if not pem:
        raise ValueError("empty PEM")
    key = serialization.load_pem_public_key(pem.encode("utf-8"))
    if not isinstance(key, Ed25519PublicKey):
        raise ValueError("TELLER_CONNECT_SIGNING_PUBLIC_KEY must be an Ed25519 public key (PEM)")
    return key


def verify_enrollment_signatures(
    *,
    public_key: Ed25519PublicKey,
    nonce: str,
    access_token: str,
    teller_user_id: str,
    enrollment_id: str,
    environment: str,
    signatures: list[str],
) -> bool:
    """Verify at least one Teller Connect enrollment signature (Ed25519).

    Teller signs a payload derived from
    ``nonce``, ``accessToken``, ``userId``, ``enrollmentId``, and ``environment``.
    We try the dot-concatenated UTF-8 string and its SHA-256 digest to tolerate
    spec wording differences.
    """
    dot = f"{nonce}.{access_token}.{teller_user_id}.{enrollment_id}.{environment}".encode("utf-8")
    candidates: tuple[bytes, ...] = (dot, hashlib.sha256(dot).digest())

    for sig_b64 in signatures:
        if not sig_b64 or not isinstance(sig_b64, str):
            continue
        raw = sig_b64.strip()
        for decoder in (base64.b64decode, base64.urlsafe_b64decode):
            pad = (4 - len(raw) % 4) % 4
            try:
                sig = decoder(raw + "=" * pad)
            except (binascii.Error, ValueError):
                continue
            if len(sig) != 64:
                continue
            for msg in candidates:
                try:
                    public_key.verify(sig, msg)
                    return True
                except Exception:
                    continue
    return False
