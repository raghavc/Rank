from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class ConnectTokenResponse(BaseModel):
    application_id: str
    environment: str


class BankLinkRequest(BaseModel):
    """Link one or more Teller accounts for the authenticated user.

    When `teller_account_id` is omitted, the server calls Teller's ``GET /accounts``
    endpoint (using developer mTLS) and links every eligible depository
    *checking* or *savings* account — mirroring Connect's behaviour when multiple
    accounts are enrolled under the same access token.

    Passing `teller_account_id` + `account_subtype` directly is kept for backwards
    compatibility or future clients that already enumerated accounts locally.
    """

    teller_access_token: str = Field(min_length=1)
    teller_account_id: str | None = None
    institution_name: str | None = None
    last_four: str | None = None
    account_type: str | None = Field(default="depository")
    account_subtype: str | None = None  # "checking" | "savings" — inferred server-side when omitted


class BankAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_name: str | None
    account_subtype: str | None
    last_four: str | None
    is_active: bool
