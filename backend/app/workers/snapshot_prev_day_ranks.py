from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy import select

from app.db import SyncSessionLocal
from app.models import BalanceHistory, User
from app.services import leaderboard as lb
from app.workers.celery_app import celery_app


logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.snapshot_prev_day_ranks.snapshot_previous_day_ranks")
def snapshot_previous_day_ranks() -> dict[str, str | int]:
    """
    Build prior-calendar-day ranks from BalanceHistory (snapshot_date = yesterday UTC)
    and store in Redis HASHes for API lookups.
    """
    d = date.today() - timedelta(days=1)
    with SyncSessionLocal() as session:
        rows = session.execute(
            select(BalanceHistory.user_id, BalanceHistory.amount, User.age_bucket).join(
                User, User.id == BalanceHistory.user_id
            ).where(BalanceHistory.snapshot_date == d)
        ).all()

    if not rows:
        lb.write_previous_day_ranks({}, {})
        logger.info("snapshot_previous_day_ranks: no rows for %s", d)
        return {"snapshot_date": str(d), "users": 0}

    global_list: list[tuple[str, float]] = []
    by_bucket: dict[str, list[tuple[str, float]]] = defaultdict(list)

    for user_id, amount, bucket in rows:
        uid_str = str(user_id)
        amt = float(amount or 0)
        global_list.append((uid_str, amt))
        by_bucket[bucket].append((uid_str, amt))

    global_list.sort(key=lambda x: (-x[1], x[0]))
    global_ranks = {uid: rank for rank, (uid, _) in enumerate(global_list, start=1)}

    age_ranks: dict[str, dict[str, int]] = {}
    for bucket, lst in by_bucket.items():
        lst.sort(key=lambda x: (-x[1], x[0]))
        age_ranks[bucket] = {uid: rank for rank, (uid, _) in enumerate(lst, start=1)}

    lb.write_previous_day_ranks(global_ranks, age_ranks)
    logger.info(
        "snapshot_previous_day_ranks: %s users on %s (global), %s age buckets",
        len(global_ranks),
        d,
        len(age_ranks),
    )
    return {"snapshot_date": str(d), "users": len(global_ranks)}
