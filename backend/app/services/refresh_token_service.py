from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import RefreshToken, User


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def new_refresh_token_plaintext() -> str:
    return secrets.token_urlsafe(48)


async def issue_refresh_token(db: AsyncSession, user_id: uuid.UUID) -> str:
    s = get_settings()
    raw = new_refresh_token_plaintext()
    h = hash_refresh_token(raw)
    exp = datetime.now(timezone.utc) + timedelta(days=s.jwt_refresh_ttl_days)
    db.add(RefreshToken(user_id=user_id, token_hash=h, expires_at=exp))
    await db.flush()
    return raw


async def rotate_refresh_token(
    db: AsyncSession, refresh_plain: str
) -> tuple[User, str] | None:
    """Validate refresh token, delete the row (one-time use), return user + new refresh."""
    h = hash_refresh_token(refresh_plain.strip())
    row = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == h))
    if row is None:
        return None
    now = datetime.now(timezone.utc)
    exp = row.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp <= now:
        await db.delete(row)
        await db.commit()
        return None
    user = await db.get(User, row.user_id)
    if user is None or not user.is_active:
        await db.delete(row)
        await db.commit()
        return None
    await db.delete(row)
    await db.flush()
    new_raw = await issue_refresh_token(db, user.id)
    await db.commit()
    await db.refresh(user)
    return user, new_raw
