from __future__ import annotations

import logging

from sqlalchemy import select

from app.db import SyncSessionLocal
from app.models import Balance, User
from app.services import leaderboard as lb
from app.workers.celery_app import celery_app


logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.recompute_leaderboard.recompute_leaderboard")
def recompute_leaderboard() -> dict[str, int]:
    """Wipe all leaderboard sets and rebuild from the balances table."""
    import redis

    from app.config import get_settings

    r = redis.Redis.from_url(get_settings().redis_url, decode_responses=True)
    lb.snapshot_current_ranks(r=r)
    lb.reset_all(r=r)

    with SyncSessionLocal() as session:
        rows = session.execute(
            select(User.id, User.age_bucket, Balance.total_amount)
            .join(Balance, Balance.user_id == User.id)
            .where(User.is_active.is_(True))
        ).all()

    if not rows:
        return {"users_indexed": 0}

    pipe = r.pipeline()
    for user_id, bucket, total in rows:
        score = float(total or 0)
        pipe.zadd(lb.GLOBAL_KEY, {str(user_id): score})
        pipe.zadd(lb.age_key(bucket), {str(user_id): score})
    pipe.execute()

    logger.info("recomputed leaderboard for %d users", len(rows))
    return {"users_indexed": len(rows)}
