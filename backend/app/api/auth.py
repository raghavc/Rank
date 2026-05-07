from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import Balance, User
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse
from app.schemas.user import MeResponse
from app.services.age_bucket import bucket_for
from app.services.jwt_service import create_access_token, hash_password, verify_password
from app.services.username_generator import generate_unique


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: SignupRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    try:
        bucket = bucket_for(body.dob)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e)) from e

    existing = await db.scalar(select(User.id).where(User.email == body.email.lower()))
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "email already in use")

    username = await generate_unique(db)
    user = User(
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        username=username,
        dob=body.dob,
        age_bucket=bucket,
    )
    db.add(user)
    try:
        await db.flush()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "could not create user") from e

    db.add(Balance(user_id=user.id))
    await db.commit()

    return TokenResponse(
        access_token=create_access_token(user.id),
        username=user.username,
        age_bucket=user.age_bucket,
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = await db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")

    user.last_active_at = datetime.now(timezone.utc)
    await db.commit()

    return TokenResponse(
        access_token=create_access_token(user.id),
        username=user.username,
        age_bucket=user.age_bucket,
    )


@router.get("/me", response_model=MeResponse)
async def me(
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeResponse:
    has_bank = await db.scalar(
        select(User.id).join(User.bank_accounts).where(
            User.id == current.id
        ).limit(1)
    )
    return MeResponse(
        username=current.username,
        age_bucket=current.age_bucket,
        has_bank_linked=has_bank is not None,
    )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_me(
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Permanently delete the user and all their data (balances, accounts)."""
    from app.services.leaderboard import remove as lb_remove

    try:
        lb_remove(current.id, current.age_bucket)
    except Exception:
        # Redis being unavailable shouldn't block account deletion.
        pass
    await db.delete(current)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
