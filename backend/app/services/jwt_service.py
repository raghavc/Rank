from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import jwt

from app.config import get_settings


class TokenError(Exception):
    pass


def create_access_token(user_id: uuid.UUID) -> str:
    s = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=s.jwt_ttl_hours)).timestamp()),
    }
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_alg)


def decode_token(token: str) -> uuid.UUID:
    s = get_settings()
    try:
        payload = jwt.decode(token, s.jwt_secret, algorithms=[s.jwt_alg])
    except jwt.PyJWTError as e:
        raise TokenError(str(e)) from e
    sub = payload.get("sub")
    if not sub:
        raise TokenError("missing sub")
    try:
        return uuid.UUID(sub)
    except ValueError as e:
        raise TokenError("invalid sub") from e


def hash_password(password: str) -> str:
    import bcrypt

    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, hashed: str) -> bool:
    import bcrypt

    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False
