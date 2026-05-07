from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, limiter
from app.models import Balance, User
from app.schemas.leaderboard import (
    LeaderboardEntry,
    LeaderboardListResponse,
    LeaderboardMe,
)
from app.services import leaderboard as lb


router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

Scope = Literal["global", "age"]


def _delta_pct(current: Decimal, previous: Decimal) -> float:
    if previous == 0:
        return 0.0 if current == 0 else 100.0
    return float((current - previous) / previous * 100)


async def _db_rank_and_total(
    *,
    current: User,
    db: AsyncSession,
    scope: Scope,
    current_total: Decimal,
) -> tuple[int | None, int]:
    filters = [User.is_active.is_(True)]
    if scope == "age":
        filters.append(User.age_bucket == current.age_bucket)

    total = await db.scalar(
        select(func.count())
        .select_from(User)
        .where(*filters)
    )
    total = int(total or 0)
    if total == 0:
        return None, 0

    higher = await db.scalar(
        select(func.count())
        .select_from(User)
        .join(Balance, Balance.user_id == User.id, isouter=True)
        .where(
            *filters,
            User.id != current.id,
            func.coalesce(Balance.total_amount, Decimal("0")) > current_total,
        )
    )
    return int(higher or 0) + 1, total


async def _db_top(
    *,
    db: AsyncSession,
    scope: Scope,
    current: User,
    limit: int,
) -> tuple[list[LeaderboardEntry], int]:
    filters = [User.is_active.is_(True)]
    if scope == "age":
        filters.append(User.age_bucket == current.age_bucket)

    total = await db.scalar(
        select(func.count())
        .select_from(User)
        .where(*filters)
    )
    total = int(total or 0)
    if total == 0:
        return [], 0

    rows = await db.execute(
        select(User.id, User.username, Balance.total_amount, Balance.previous_amount)
        .join(Balance, Balance.user_id == User.id, isouter=True)
        .where(*filters)
        .order_by(func.coalesce(Balance.total_amount, Decimal("0")).desc(), User.username.asc())
        .limit(limit)
    )

    entries: list[LeaderboardEntry] = []
    for idx, row in enumerate(rows, start=1):
        balance = row.total_amount or Decimal("0")
        previous = row.previous_amount or Decimal("0")
        previous_rank: int | None
        try:
            previous_rank = lb.get_previous_day_rank(row.id, scope, current.age_bucket)
        except Exception:
            previous_rank = None
        entries.append(
            LeaderboardEntry(
                rank=idx,
                previous_rank=previous_rank,
                username=row.username,
                balance=balance,
                delta_pct=_delta_pct(balance, previous),
            )
        )
    return entries, total


@limiter.limit("10/minute")
@router.get("/me", response_model=LeaderboardMe)
async def my_rank(
    request: Request,  # noqa: ARG001 - required by slowapi
    scope: str = Query("global", pattern="^(global|age)$"),
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LeaderboardMe:
    bal = await db.get(Balance, current.id)
    total_amount = bal.total_amount if bal else Decimal("0")
    previous_amount = bal.previous_amount if bal else Decimal("0")

    try:
        rank = lb.get_rank(current.id, scope, current.age_bucket)
        total = lb.get_total(scope, current.age_bucket)
        previous_rank = lb.get_previous_day_rank(current.id, scope, current.age_bucket)
        if total == 0:
            rank, total = await _db_rank_and_total(
                current=current,
                db=db,
                scope=scope,
                current_total=total_amount,
            )
    except Exception:
        rank, total = await _db_rank_and_total(
            current=current,
            db=db,
            scope=scope,
            current_total=total_amount,
        )
        previous_rank = None

    delta_amount = total_amount - previous_amount
    return LeaderboardMe(
        rank=rank,
        previous_rank=previous_rank,
        total_users=total,
        balance=total_amount,
        previous_balance=previous_amount,
        delta_amount=delta_amount,
        delta_pct=_delta_pct(total_amount, previous_amount),
        scope=scope,
    )


@limiter.limit("10/minute")
@router.get("", response_model=LeaderboardListResponse)
async def leaderboard_list(
    request: Request,  # noqa: ARG001
    scope: str = Query("global", pattern="^(global|age)$"),
    limit: int = Query(50, ge=1, le=100),
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LeaderboardListResponse:
    try:
        top = lb.get_top(scope, current.age_bucket, limit)
    except Exception:
        top = []
    if not top:
        entries, total = await _db_top(db=db, scope=scope, current=current, limit=limit)
        return LeaderboardListResponse(scope=scope, total_users=total, entries=entries)

    user_ids = [uuid.UUID(uid) for uid, _ in top]
    rows = await db.execute(
        select(User.id, User.username, Balance.total_amount, Balance.previous_amount)
        .join(Balance, Balance.user_id == User.id, isouter=True)
        .where(User.id.in_(user_ids))
    )
    by_id = {
        r.id: (r.username, r.total_amount or Decimal("0"), r.previous_amount or Decimal("0"))
        for r in rows
    }

    entries: list[LeaderboardEntry] = []
    for idx, (uid_str, _score) in enumerate(top, start=1):
        user_id = uuid.UUID(uid_str)
        info = by_id.get(user_id)
        if info is None:
            continue
        username, balance, previous = info
        try:
            previous_rank = lb.get_previous_day_rank(user_id, scope, current.age_bucket)
        except Exception:
            previous_rank = None
        entries.append(
            LeaderboardEntry(
                rank=idx,
                previous_rank=previous_rank,
                username=username,
                balance=balance,
                delta_pct=_delta_pct(balance, previous),
            )
        )

    try:
        total_users = lb.get_total(scope, current.age_bucket)
    except Exception:
        _entries, total_users = await _db_top(db=db, scope=scope, current=current, limit=limit)

    return LeaderboardListResponse(
        scope=scope,
        total_users=total_users,
        entries=entries,
    )
