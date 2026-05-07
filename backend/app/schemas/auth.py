from __future__ import annotations

import re
from datetime import date

from pydantic import BaseModel, EmailStr, Field, field_validator

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


class SignupRequest(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    dob: date

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str | None) -> str | None:
        if value is None:
            return None
        s = value.strip().lower()
        if len(s) < 3 or len(s) > 50:
            raise ValueError("username must be between 3 and 50 characters")
        if _USERNAME_RE.fullmatch(s) is None:
            raise ValueError(
                "username may only contain letters, digits, underscores, and hyphens"
            )
        return s


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"
    username: str
    age_bucket: str


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10, max_length=2048)


class LogoutRequest(BaseModel):
    """If ``refresh_token`` is set, revoke only that session; otherwise revoke all refresh tokens and invalidate access JWTs."""

    refresh_token: str | None = None
