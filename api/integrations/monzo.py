"""Monzo read-only client (MECHANICAL / plumbing only).

Talks HTTP to Monzo and hands back raw JSON / a GBP total. Knows nothing about
Finka's models or DB — aggregation lives in services/net_worth_service.py.

AUTH: a direct access token from the Monzo developer playground
(https://developers.monzo.com/), used as a bearer token. Simple, but these
tokens EXPIRE after a few hours and have no refresh path here — when it goes
stale (401) paste a fresh token into MONZO_ACCESS_TOKEN. We read one configured
account (MONZO_ACCOUNT_ID) so we never hit /accounts, which can 403 until API
access is approved in the app.

Balances come back in minor units (pennies) — we divide by 100.
"""

import logging
from decimal import Decimal

import httpx

from config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.monzo.com"


class MonzoError(RuntimeError):
    """Raised when the Monzo API returns an unrecoverable error."""


class MonzoClient:
    def __init__(
        self,
        *,
        access_token: str | None = None,
        account_id: str | None = None,
        timeout: float = 15.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.access_token = access_token if access_token is not None else settings.monzo_access_token
        self.account_id = account_id if account_id is not None else settings.monzo_account_id
        self.timeout = timeout
        self._transport = transport

    @property
    def configured(self) -> bool:
        return bool(self.access_token and self.account_id)

    async def _get(self, path: str, params: dict | None = None) -> dict:
        headers = {"Authorization": f"Bearer {self.access_token}"}
        async with httpx.AsyncClient(timeout=self.timeout, transport=self._transport) as client:
            resp = await client.get(f"{BASE_URL}{path}", headers=headers, params=params)
        if resp.status_code == 401:
            raise MonzoError(
                "Monzo rejected the access token (401). Playground tokens expire — "
                "grab a fresh one from developers.monzo.com and update MONZO_ACCESS_TOKEN."
            )
        if resp.status_code == 403:
            raise MonzoError(
                "Monzo returned 403. Approve API access in the Monzo app (Settings), then retry."
            )
        resp.raise_for_status()
        return resp.json()

    async def fetch_balance(self) -> dict:
        """Balance for the configured account: {balance, total_balance, currency} in minor units."""
        return await self._get("/balance", params={"account_id": self.account_id})

    async def total_gbp(self) -> Decimal:
        """Pots only, in GBP — excludes the spendable current account.

        pots = total_balance - balance (total_balance = current account + pots).
        We deliberately drop the current-account portion: for net-worth/long-term
        savings we only want money set aside in pots.
        """
        bal = await self.fetch_balance()
        total = Decimal(str(bal.get("total_balance", bal.get("balance", 0))))
        current = Decimal(str(bal.get("balance", 0)))
        pots_minor = max(total - current, Decimal("0"))
        return pots_minor / Decimal("100")
