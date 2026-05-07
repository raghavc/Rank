import base64
import os

import pytest

# Set required env vars BEFORE importing crypto, since get_settings() reads at import time.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("ALEMBIC_DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET", "x" * 48)
os.environ.setdefault(
    "TELLER_TOKEN_ENC_KEY", base64.b64encode(b"\x01" * 32).decode("ascii")
)


def test_roundtrip() -> None:
    from app.services.crypto import decrypt, encrypt

    blob = encrypt("hello world")
    assert decrypt(blob) == "hello world"


def test_each_encrypt_unique() -> None:
    from app.services.crypto import encrypt

    a = encrypt("same")
    b = encrypt("same")
    assert a != b  # different nonces -> different ciphertexts


def test_bad_key_raises() -> None:
    from app.services import crypto

    saved = os.environ["TELLER_TOKEN_ENC_KEY"]
    os.environ["TELLER_TOKEN_ENC_KEY"] = base64.b64encode(b"\x01" * 16).decode("ascii")
    crypto.get_settings.cache_clear()  # type: ignore[attr-defined]
    try:
        with pytest.raises(ValueError):
            crypto.encrypt("foo")
    finally:
        os.environ["TELLER_TOKEN_ENC_KEY"] = saved
        crypto.get_settings.cache_clear()  # type: ignore[attr-defined]
