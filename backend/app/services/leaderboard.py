from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Literal

import redis

from app.config import get_settings


Scope = Literal["global", "age"]


GLOBAL_KEY = "leaderboard:global"
PREV_GLOBAL_KEY = "leaderboard:prev:global"


def age_key(bucket: str) -> str:
    return f"leaderboard:age:{bucket}"


def prev_age_key(bucket: str) -> str:
    return f"leaderboard:prev:age:{bucket}"


def _redis() -> redis.Redis:
    return redis.Redis.from_url(get_settings().redis_url, decode_responses=True)


def _key_for(scope: Scope, age_bucket: str) -> str:
    return GLOBAL_KEY if scope == "global" else age_key(age_bucket)


def snapshot_current_ranks(*, r: redis.Redis | None = None) -> None:
    r = r or _redis()

    global_members = r.zrevrange(GLOBAL_KEY, 0, -1)
    global_ranks = {uid: rank for rank, uid in enumerate(global_members, start=1)}

    age_ranks: dict[str, dict[str, int]] = {}
    for key in r.scan_iter("leaderboard:age:*"):
        bucket = key.split("leaderboard:age:", 1)[1]
        members = r.zrevrange(key, 0, -1)
        age_ranks[bucket] = {uid: rank for rank, uid in enumerate(members, start=1)}

    write_previous_day_ranks(global_ranks, age_ranks, r=r)


def upsert(user_id: uuid.UUID, balance: Decimal, age_bucket: str, *, r: redis.Redis | None = None) -> None:
    r = r or _redis()
    snapshot_current_ranks(r=r)
    score = float(balance)
    pipe = r.pipeline()
    pipe.zadd(GLOBAL_KEY, {str(user_id): score})
    pipe.zadd(age_key(age_bucket), {str(user_id): score})
    pipe.execute()


def remove(user_id: uuid.UUID, age_bucket: str, *, r: redis.Redis | None = None) -> None:
    r = r or _redis()
    snapshot_current_ranks(r=r)
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


def get_previous_day_rank(
    user_id: uuid.UUID,
    scope: Scope,
    age_bucket: str,
    *,
    r: redis.Redis | None = None,
) -> int | None:
    r = r or _redis()
    key = PREV_GLOBAL_KEY if scope == "global" else prev_age_key(age_bucket)
    raw = r.hget(key, str(user_id))
    return None if raw is None else int(raw)


def write_previous_day_ranks(
    global_ranks: dict[str, int],
    age_ranks: dict[str, dict[str, int]],
    *,
    r: redis.Redis | None = None,
) -> None:
    r = r or _redis()
    keys = [PREV_GLOBAL_KEY, *[prev_age_key(bucket) for bucket in age_ranks]]
    if keys:
        r.delete(*keys)
    pipe = r.pipeline()
    if global_ranks:
        pipe.hset(PREV_GLOBAL_KEY, mapping=global_ranks)
    for bucket, ranks in age_ranks.items():
        if ranks:
            pipe.hset(prev_age_key(bucket), mapping=ranks)
    pipe.execute()


def reset_all(*, r: redis.Redis | None = None) -> None:
    """Wipe only the live leaderboard sorted sets — preserve previous-rank snapshots."""
    r = r or _redis()
    keys = [GLOBAL_KEY]
    keys.extend(list(r.scan_iter("leaderboard:age:*")))
    if keys:
        r.delete(*keys)
