from __future__ import annotations

import asyncio
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.config import get_settings
from app.models import BankAccount, User
from app.schemas.bank import BankAccountOut, BankLinkRequest, ConnectTokenResponse
from app.services.crypto import encrypt
from app.services.teller import TellerError, TellerTokenExpired, fetch_linkable_accounts


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bank", tags=["bank"])


_ALLOWED_SUBTYPES = {"checking", "savings"}


@router.post("/connect-token", response_model=ConnectTokenResponse)
async def connect_token(_: User = Depends(get_current_user)) -> ConnectTokenResponse:
    s = get_settings()
    # Reject empty values AND the .env.example placeholder so the iOS app
    # gets a clear 503 instead of a confusing "internal server error"
    # surfacing inside Teller's hosted widget.
    if not s.teller_app_id or s.teller_app_id == "your_teller_app_id":
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "TELLER_APP_ID not configured on the server",
        )
    return ConnectTokenResponse(
        application_id=s.teller_app_id, environment=s.teller_environment
    )


@router.post("/link", response_model=BankAccountOut, status_code=status.HTTP_201_CREATED)
async def link_bank(
    body: BankLinkRequest,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BankAccountOut:
    token = body.teller_access_token
    manual_id = (body.teller_account_id or "").strip() or None

    if manual_id is not None:
        if not body.account_subtype:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "`account_subtype` is required when `teller_account_id` is provided",
            )

        acc_type = (body.account_type or "depository").lower()
        if acc_type != "depository":
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"only depository accounts are supported (got {body.account_type})",
            )
        subtype = (body.account_subtype or "").lower()
        if subtype not in _ALLOWED_SUBTYPES:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"only checking/savings accounts are supported (got {body.account_subtype})",
            )

        resolved_rows: list[dict[str, str | None]] = [
            {
                "id": manual_id,
                "type": acc_type,
                "subtype": subtype,
                "last_four": body.last_four,
                "institution_name": body.institution_name,
            }
        ]
    else:
        try:
            fetched = await asyncio.to_thread(fetch_linkable_accounts, token)
        except TellerTokenExpired as e:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                "teller rejected the access token (expired or invalid credentials)",
            ) from e
        except TellerError as e:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(e)) from e

        if not fetched:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Teller returned no checking or savings accounts for this enrollment.",
            )

        fallback_inst = body.institution_name
        resolved_rows = [
            {
                "id": row["id"],
                "type": row["type"],
                "subtype": row["subtype"],
                "last_four": row.get("last_four") or body.last_four,
                "institution_name": row.get("institution_name") or fallback_inst,
            }
            for row in fetched
        ]

    encrypted = encrypt(token)
    created: list[BankAccount] = []

    try:
        for row in resolved_rows:
            ba = BankAccount(
                user_id=current.id,
                teller_account_id=str(row["id"]),
                teller_access_token_encrypted=encrypted,
                institution_name=row.get("institution_name"),
                account_type=str(row["type"] or "depository").lower(),
                account_subtype=str(row["subtype"]).lower(),
                last_four=row.get("last_four"),
                is_active=True,
            )
            db.add(ba)
            created.append(ba)

        await db.commit()
        for ba in created:
            await db.refresh(ba)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "account already linked")

    # Fire an immediate background refresh for this user.
    try:
        from app.workers.refresh_balances import refresh_user_balance

        refresh_user_balance.delay(str(current.id))
    except Exception:  # pragma: no cover - broker connection issues are non-fatal
        logger.exception("failed to enqueue refresh_user_balance")

    return BankAccountOut.model_validate(created[0])


@router.get("/accounts", response_model=list[BankAccountOut])
async def list_accounts(
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[BankAccountOut]:
    rows = await db.scalars(
        select(BankAccount).where(BankAccount.user_id == current.id)
    )
    return [BankAccountOut.model_validate(a) for a in rows]


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def disconnect_account(
    account_id: uuid.UUID,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    account = await db.get(BankAccount, account_id)
    if account is None or account.user_id != current.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "account not found")
    await db.delete(account)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
