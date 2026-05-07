from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, limiter
from app.config import get_settings
from app.models import Balance, RefreshToken, User
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    SignupRequest,
    TokenResponse,
)
from app.schemas.user import MeResponse
from app.services.age_bucket import bucket_for
from app.services.jwt_service import create_access_token, hash_password, verify_password
from app.services.refresh_token_service import (
    hash_refresh_token,
    issue_refresh_token,
    rotate_refresh_token,
)
from app.services.username_generator import generate_unique


router = APIRouter(prefix="/auth", tags=["auth"])


async def _build_token_response(db: AsyncSession, user: User) -> TokenResponse:
    s = get_settings()
    await db.refresh(user, attribute_names=["token_version"])
    access = create_access_token(user.id, token_version=user.token_version)
    refresh_plain = await issue_refresh_token(db, user.id)
    await db.commit()
    return TokenResponse(
        access_token=access,
        refresh_token=refresh_plain,
        expires_in=s.jwt_access_ttl_minutes * 60,
        username=user.username,
        age_bucket=user.age_bucket,
    )


@limiter.limit("5/minute")
@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: Request,
    body: SignupRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    try:
        bucket = bucket_for(body.dob)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e)) from e

    existing = await db.scalar(select(User.id).where(User.email == body.email.lower()))
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "email already in use")

    username = body.username or await generate_unique(db)
    username_taken = await db.scalar(select(User.id).where(User.username == username))
    if username_taken is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "username already taken")

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
    await db.refresh(user)
    return await _build_token_response(db, user)


@limiter.limit("10/minute")
@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    user = await db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")

    user.last_active_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)
    return await _build_token_response(db, user)


@limiter.limit("30/minute")
@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    request: Request,
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    rotated = await rotate_refresh_token(db, body.refresh_token)
    if rotated is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid refresh token")
    user, new_refresh = rotated
    s = get_settings()
    access = create_access_token(user.id, token_version=user.token_version)
    return TokenResponse(
        access_token=access,
        refresh_token=new_refresh,
        expires_in=s.jwt_access_ttl_minutes * 60,
        username=user.username,
        age_bucket=user.age_bucket,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def logout(
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    body: LogoutRequest | None = Body(None),
) -> Response:
    data = body or LogoutRequest()
    if data.refresh_token:
        h = hash_refresh_token(data.refresh_token)
        await db.execute(
            delete(RefreshToken).where(
                RefreshToken.token_hash == h,
                RefreshToken.user_id == current.id,
            )
        )
    else:
        current.token_version += 1
        await db.execute(delete(RefreshToken).where(RefreshToken.user_id == current.id))
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=MeResponse)
async def me(
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeResponse:
    has_bank = await db.scalar(
        select(User.id).join(User.bank_accounts).where(User.id == current.id).limit(1)
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
