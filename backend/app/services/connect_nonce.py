from __future__ import annotations

import asyncio
import time
from typing import Final

from app.config import get_settings

_TTL_SEC: Final[int] = 15 * 60
_memory_store: dict[str, tuple[str, float]] = {}


def _memory_set(nonce: str, user_id: str) -> None:
    _memory_store[nonce] = (user_id, time.monotonic() + float(_TTL_SEC))


def _memory_consume(nonce: str, expected_user_id: str) -> bool:
    entry = _memory_store.pop(nonce, None)
    if entry is None:
        return False
    uid, deadline = entry
    if time.monotonic() > deadline:
        return False
    return uid == expected_user_id


async def store_connect_nonce(*, user_id: str, nonce: str) -> None:
    s = get_settings()
    if s.use_memory_nonce_store:
        _memory_set(nonce, user_id)
        return

    def _sync() -> None:
        import redis

        r = redis.Redis.from_url(s.redis_url, decode_responses=True)
        try:
            r.setex(f"rank:connect_nonce:{nonce}", _TTL_SEC, user_id)
        finally:
            r.close()

    await asyncio.to_thread(_sync)


async def consume_connect_nonce(*, nonce: str, expected_user_id: str) -> bool:
    s = get_settings()
    if s.use_memory_nonce_store:
        return _memory_consume(nonce, expected_user_id)

    def _sync() -> bool:
        import redis

        r = redis.Redis.from_url(s.redis_url, decode_responses=True)
        try:
            pipe = r.pipeline()
            pipe.get(f"rank:connect_nonce:{nonce}")
            pipe.delete(f"rank:connect_nonce:{nonce}")
            got, _ = pipe.execute()
            if not got:
                return False
            return str(got) == expected_user_id
        finally:
            r.close()

    return await asyncio.to_thread(_sync)
