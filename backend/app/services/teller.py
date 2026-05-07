from __future__ import annotations

from decimal import Decimal
from typing import Any

import httpx

from app.config import get_settings


class TellerError(Exception):
    pass


class TellerTokenExpired(TellerError):
    pass


def institution_name(acc: dict[str, Any]) -> str | None:
    inst = acc.get("institution")
    if isinstance(inst, dict):
        name = inst.get("name")
        return str(name) if name else None
    return None


def fetch_linkable_accounts(access_token: str) -> list[dict[str, Any]]:
    """
    Calls Teller ``GET /accounts`` and extracts every eligible depository
    *checking* or *savings* row.

    Returns sorted list of lightweight dicts: ``id``, ``type``, ``subtype``,
    ``last_four``, ``institution_name``.
    """
    with TellerClient(access_token) as client:
        raw = client.list_accounts()

    bucket: list[dict[str, Any]] = []
    for a in raw:
        tp = str(a.get("type", "") or "").lower()
        st = str(a.get("subtype", "") or "").lower()
        if tp != "depository" or st not in {"checking", "savings"}:
            continue

        aid = a.get("id")
        if not aid:
            continue

        mask = a.get("last_four") if a.get("last_four") is not None else a.get("mask")
        last_four = str(mask) if mask not in (None, "") else None

        bucket.append(
            {
                "id": str(aid),
                "type": tp,
                "subtype": st,
                "last_four": last_four,
                "institution_name": institution_name(a),
            }
        )

    bucket.sort(key=lambda row: row["id"])
    return bucket


class TellerClient:
    """
    Synchronous Teller API client for use in Celery tasks and immediate
    post-link balance fetches. Uses mTLS + HTTP Basic auth (token, "").
    """

    BASE_URL = "https://api.teller.io"
    TIMEOUT = 10.0

    def __init__(self, access_token: str):
        s = get_settings()
        self._client = httpx.Client(
            base_url=self.BASE_URL,
            cert=(s.teller_cert_path, s.teller_key_path),
            auth=(access_token, ""),
            timeout=self.TIMEOUT,
            headers={"Accept": "application/json"},
        )

    def __enter__(self) -> "TellerClient":
        return self

    def __exit__(self, *_: object) -> None:
        self._client.close()

    def close(self) -> None:
        self._client.close()

    def _get(self, path: str) -> Any:
        try:
            r = self._client.get(path)
        except httpx.HTTPError as e:
            raise TellerError(f"network error calling {path}: {e}") from e
        if r.status_code == 401:
            raise TellerTokenExpired(f"401 from {path}")
        if r.status_code >= 400:
            raise TellerError(f"{r.status_code} from {path}: {r.text[:200]}")
        return r.json()

    def list_accounts(self) -> list[dict[str, Any]]:
        return self._get("/accounts")

    def get_balance(self, account_id: str) -> dict[str, Any]:
        return self._get(f"/accounts/{account_id}/balances")


def parse_balance(payload: dict[str, Any]) -> Decimal:
    """
    Teller returns strings like '1234.56'. Prefer ledger over available
    so unsettled debits don't dip the leaderboard temporarily.
    """
    raw = payload.get("ledger") or payload.get("available") or "0"
    try:
        return Decimal(str(raw))
    except Exception:
        return Decimal("0")
