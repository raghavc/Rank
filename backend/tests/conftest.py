"""Shared test fixtures.

We seed environment variables BEFORE the app modules are imported so
`get_settings()` doesn't blow up looking for a real `.env` file.
"""

from __future__ import annotations

import base64
import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("ALEMBIC_DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET", "x" * 48)
os.environ.setdefault(
    "TELLER_TOKEN_ENC_KEY", base64.b64encode(b"\x01" * 32).decode("ascii")
)
