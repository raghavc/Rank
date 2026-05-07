from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class LeaderboardEntry(BaseModel):
    rank: int
    username: str
    balance: Decimal
    delta_pct: float


class LeaderboardListResponse(BaseModel):
    scope: str
    total_users: int
    entries: list[LeaderboardEntry]


class LeaderboardMe(BaseModel):
    rank: int | None
    total_users: int
    balance: Decimal
    previous_balance: Decimal
    delta_amount: Decimal
    delta_pct: float
    scope: str
