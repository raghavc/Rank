from __future__ import annotations

import logging
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db import SyncSessionLocal
from app.models import Balance, BalanceHistory, BankAccount, User
from app.services.crypto import decrypt
from app.services.teller import TellerClient, TellerTokenExpired, parse_balance
from app.workers.celery_app import celery_app


logger = logging.getLogger(__name__)


def _refresh_for_user(session, user_id: uuid.UUID) -> Decimal:
    accounts: list[BankAccount] = list(
        session.scalars(
            select(BankAccount).where(
                BankAccount.user_id == user_id, BankAccount.is_active.is_(True)
            )
        )
    )
    if not accounts:
        return Decimal("0")

    total = Decimal("0")
    for account in accounts:
        try:
            token = decrypt(account.teller_access_token_encrypted)
        except Exception:
            logger.exception("crypto failure for account %s", account.id)
            account.is_active = False
            continue

        try:
            with TellerClient(token) as client:
                payload = client.get_balance(account.teller_account_id)
        except TellerTokenExpired:
            logger.warning(
                "teller token expired for account %s — marking inactive", account.id
            )
            account.is_active = False
            continue
        except Exception:
            logger.exception("teller error for account %s", account.id)
            continue

        total += parse_balance(payload)

    bal = session.get(Balance, user_id)
    if bal is None:
        bal = Balance(user_id=user_id, total_amount=Decimal("0"), previous_amount=Decimal("0"))
        session.add(bal)
        session.flush()

    bal.previous_amount = bal.total_amount
    bal.total_amount = total

    stmt = (
        pg_insert(BalanceHistory)
        .values(user_id=user_id, amount=total, snapshot_date=date.today())
        .on_conflict_do_update(
            index_elements=[BalanceHistory.user_id, BalanceHistory.snapshot_date],
            set_={"amount": total},
        )
    )
    session.execute(stmt)

    return total


@celery_app.task(name="app.workers.refresh_balances.refresh_user_balance")
def refresh_user_balance(user_id_str: str) -> dict[str, str]:
    """Refresh a single user's balance immediately and update the leaderboard."""
    from app.services import leaderboard as lb

    user_id = uuid.UUID(user_id_str)
    with SyncSessionLocal() as session:
        user = session.get(User, user_id)
        if user is None:
            return {"status": "missing_user", "user_id": user_id_str}
        total = _refresh_for_user(session, user_id)
        session.commit()
        lb.upsert(user_id, total, user.age_bucket)
    return {"status": "ok", "user_id": user_id_str, "total": str(total)}


@celery_app.task(name="app.workers.refresh_balances.refresh_all_balances")
def refresh_all_balances() -> dict[str, int]:
    """Daily sweep: refresh every user's balance, then recompute the leaderboard."""
    from app.workers.recompute_leaderboard import recompute_leaderboard

    with SyncSessionLocal() as session:
        user_ids = list(
            session.scalars(
                select(User.id).where(User.is_active.is_(True)).order_by(User.id)
            )
        )

    refreshed = 0
    for uid in user_ids:
        with SyncSessionLocal() as session:
            try:
                _refresh_for_user(session, uid)
                session.commit()
                refreshed += 1
            except Exception:
                session.rollback()
                logger.exception("failed to refresh user %s", uid)

    recompute_leaderboard.delay()
    return {"users_refreshed": refreshed, "users_seen": len(user_ids)}
