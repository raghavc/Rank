from __future__ import annotations

from pydantic import BaseModel


class MeResponse(BaseModel):
    username: str
    age_bucket: str
    has_bank_linked: bool
