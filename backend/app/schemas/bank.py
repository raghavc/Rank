from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class ConnectTokenResponse(BaseModel):
    application_id: str
    environment: str
    nonce: str | None = None


class BankLinkRequest(BaseModel):
    """Link one or more Teller accounts for the authenticated user.

    When `teller_account_id` is omitted, the server calls Teller's ``GET /accounts``
    endpoint (using developer mTLS) and links every eligible depository
    *checking* or *savings* account — mirroring Connect's behaviour when multiple
    accounts are enrolled under the same access token.

    When ``TELLER_CONNECT_SIGNING_PUBLIC_KEY`` is configured, you must pass the
    Connect ``nonce`` (from ``/bank/connect-token``) plus enrollment ``signatures``,
    ``teller_user_id``, and ``teller_enrollment_id`` from the Connect success payload.
    """

    teller_access_token: str = Field(min_length=1)
    teller_account_id: str | None = None
    institution_name: str | None = None
    last_four: str | None = None
    account_type: str | None = Field(default="depository")
    account_subtype: str | None = None

    teller_nonce: str | None = None
    teller_user_id: str | None = None
    teller_enrollment_id: str | None = None
    teller_signatures: list[str] | None = None


class BankAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_name: str | None
    account_subtype: str | None
    last_four: str | None
    is_active: bool
