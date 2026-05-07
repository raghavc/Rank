from __future__ import annotations

import hashlib
from collections.abc import AsyncIterator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from slowapi import Limiter
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import AsyncSessionLocal
from app.models import User
from app.services.jwt_service import TokenError, decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized")
    try:
        payload = decode_access_token(credentials.credentials)
    except TokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized") from None

    user = await db.get(User, payload.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized")
    if user.token_version != payload.token_version:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized")
    return user


def _rate_limit_key(request: Request) -> str:
    """Derive a non-sensitive rate-limit key (never store raw JWT/bearer)."""
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
        if token:
            digest = hashlib.sha256(token.encode("utf-8")).hexdigest()[:32]
            return f"bearer:{digest}"
    client = request.client
    host = client.host if client else "anon"
    return f"ip:{host}"


def build_limiter() -> Limiter:
    s = get_settings()
    kwargs: dict = {"key_func": _rate_limit_key}
    uri = (s.rate_limit_storage_uri or "").strip()
    if uri:
        kwargs["storage_uri"] = uri
    return Limiter(**kwargs)


limiter = build_limiter()
