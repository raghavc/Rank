from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Literal

import redis

from app.config import get_settings


Scope = Literal["global", "age"]


GLOBAL_KEY = "leaderboard:global"


def age_key(bucket: str) -> str:
    return f"leaderboard:age:{bucket}"


def _redis() -> redis.Redis:
    return redis.Redis.from_url(get_settings().redis_url, decode_responses=True)


def _key_for(scope: Scope, age_bucket: str) -> str:
    return GLOBAL_KEY if scope == "global" else age_key(age_bucket)


def upsert(user_id: uuid.UUID, balance: Decimal, age_bucket: str, *, r: redis.Redis | None = None) -> None:
    r = r or _redis()
    score = float(balance)
    pipe = r.pipeline()
    pipe.zadd(GLOBAL_KEY, {str(user_id): score})
    pipe.zadd(age_key(age_bucket), {str(user_id): score})
    pipe.execute()


def remove(user_id: uuid.UUID, age_bucket: str, *, r: redis.Redis | None = None) -> None:
    r = r or _redis()
    pipe = r.pipeline()
    pipe.zrem(GLOBAL_KEY, str(user_id))
    pipe.zrem(age_key(age_bucket), str(user_id))
    pipe.execute()


def get_rank(user_id: uuid.UUID, scope: Scope, age_bucket: str, *, r: redis.Redis | None = None) -> int | None:
    r = r or _redis()
    raw = r.zrevrank(_key_for(scope, age_bucket), str(user_id))
    return None if raw is None else int(raw) + 1


def get_total(scope: Scope, age_bucket: str, *, r: redis.Redis | None = None) -> int:
    r = r or _redis()
    return int(r.zcard(_key_for(scope, age_bucket)))


def get_top(scope: Scope, age_bucket: str, limit: int, *, r: redis.Redis | None = None) -> list[tuple[str, float]]:
    r = r or _redis()
    raw = r.zrevrange(_key_for(scope, age_bucket), 0, limit - 1, withscores=True)
    return [(uid, float(score)) for uid, score in raw]


def reset_all(*, r: redis.Redis | None = None) -> None:
    """Wipe every leaderboard key — used at the start of a recompute."""
    r = r or _redis()
    keys = list(r.scan_iter("leaderboard:*"))
    if keys:
        r.delete(*keys)
