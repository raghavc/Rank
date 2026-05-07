from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
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


@router.get("/me", response_model=LeaderboardMe)
@limiter.limit("10/minute")
async def my_rank(
    request: Request,  # noqa: ARG001 - required by slowapi
    scope: Scope = Query("global"),
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LeaderboardMe:
    bal = await db.get(Balance, current.id)
    total_amount = bal.total_amount if bal else Decimal("0")
    previous_amount = bal.previous_amount if bal else Decimal("0")

    rank = lb.get_rank(current.id, scope, current.age_bucket)
    total = lb.get_total(scope, current.age_bucket)

    delta_amount = total_amount - previous_amount
    return LeaderboardMe(
        rank=rank,
        total_users=total,
        balance=total_amount,
        previous_balance=previous_amount,
        delta_amount=delta_amount,
        delta_pct=_delta_pct(total_amount, previous_amount),
        scope=scope,
    )


@router.get("", response_model=LeaderboardListResponse)
@limiter.limit("10/minute")
async def leaderboard_list(
    request: Request,  # noqa: ARG001
    scope: Scope = Query("global"),
    limit: int = Query(50, ge=1, le=100),
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LeaderboardListResponse:
    top = lb.get_top(scope, current.age_bucket, limit)
    if not top:
        return LeaderboardListResponse(scope=scope, total_users=0, entries=[])

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
        info = by_id.get(uuid.UUID(uid_str))
        if info is None:
            continue
        username, balance, previous = info
        entries.append(
            LeaderboardEntry(
                rank=idx,
                username=username,
                balance=balance,
                delta_pct=_delta_pct(balance, previous),
            )
        )

    return LeaderboardListResponse(
        scope=scope,
        total_users=lb.get_total(scope, current.age_bucket),
        entries=entries,
    )
