from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt

from app.config import get_settings


class TokenError(Exception):
    pass


@dataclass(frozen=True)
class AccessTokenPayload:
    user_id: uuid.UUID
    jti: uuid.UUID
    token_version: int


def create_access_token(
    user_id: uuid.UUID,
    *,
    token_version: int,
    jti: uuid.UUID | None = None,
) -> str:
    s = get_settings()
    now = datetime.now(timezone.utc)
    jid = jti or uuid.uuid4()
    ttl = timedelta(minutes=s.jwt_access_ttl_minutes)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + ttl).timestamp()),
        "iss": s.jwt_iss,
        "aud": s.jwt_aud,
        "jti": str(jid),
        "tv": int(token_version),
    }
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_alg)


def decode_access_token(token: str) -> AccessTokenPayload:
    s = get_settings()
    try:
        payload = jwt.decode(
            token,
            s.jwt_secret,
            algorithms=[s.jwt_alg],
            audience=s.jwt_aud,
            issuer=s.jwt_iss,
            options={"require": ["exp", "iat", "sub", "iss", "aud", "jti", "tv"]},
        )
    except jwt.PyJWTError as e:
        raise TokenError("invalid token") from e
    sub = payload.get("sub")
    if not sub:
        raise TokenError("invalid token")
    try:
        user_id = uuid.UUID(sub)
    except ValueError as e:
        raise TokenError("invalid token") from e
    jti_raw = payload.get("jti")
    if not jti_raw:
        raise TokenError("invalid token")
    try:
        jti = uuid.UUID(str(jti_raw))
    except ValueError as e:
        raise TokenError("invalid token") from e
    tv = payload.get("tv")
    if tv is None or not isinstance(tv, (int, float)):
        raise TokenError("invalid token")
    return AccessTokenPayload(user_id=user_id, jti=jti, token_version=int(tv))


def hash_password(password: str) -> str:
    import bcrypt

    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, hashed: str) -> bool:
    import bcrypt

    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False
