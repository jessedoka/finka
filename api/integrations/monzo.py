"""Monzo read-only client (MECHANICAL / plumbing only).

Talks HTTP to Monzo and hands back raw JSON / a GBP total. Knows nothing about
Finka's models or DB — aggregation lives in services/net_worth_service.py.

AUTH: a direct access token from the Monzo developer playground
(https://developers.monzo.com/), used as a bearer token. Simple, but these
tokens EXPIRE after a few hours and have no refresh path here — when it goes
stale (401) the connection's sync health surfaces the error and the user pastes
a fresh token into the connection. We read one configured account id so we never
hit /accounts, which can 403 until API access is approved in the app.

Balances come back in minor units (pennies) — we divide by 100.
"""

import logging
import time
from decimal import Decimal

import httpx


logger = logging.getLogger(__name__)

BASE_URL = "https://api.monzo.com"
TOKEN_URL = f"{BASE_URL}/oauth2/token"
AUTH_URL = "https://auth.monzo.com/"


class MonzoError(RuntimeError):
    """Raised when the Monzo API returns an unrecoverable error."""


async def exchange_token(data: dict, *, transport: httpx.AsyncBaseTransport | None = None) -> dict:
    """POST to Monzo's token endpoint (authorization_code or refresh_token).

    Returns the raw token payload: access_token, refresh_token, expires_in, ...
    Used both by the one-time auth helper and by in-flight refresh.
    """
    async with httpx.AsyncClient(timeout=15.0, transport=transport) as client:
        resp = await client.post(TOKEN_URL, data=data)
    if resp.status_code != 200:
        raise MonzoError(f"Monzo token exchange failed ({resp.status_code}): {resp.text[:200]}")
    return resp.json()


class MonzoClient:
    def __init__(
        self,
        *,
        access_token: str | None = None,
        account_id: str | None = None,
        # OAuth refresh credentials (confidential client). When present, an
        # expired/401 access token is refreshed automatically instead of failing.
        client_id: str | None = None,
        client_secret: str | None = None,
        refresh_token: str | None = None,
        expires_at: float | None = None,
        timeout: float = 15.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.access_token = access_token or ""
        self.account_id = account_id or ""
        self.client_id = client_id or ""
        self.client_secret = client_secret or ""
        self.refresh_token = refresh_token or ""
        self.expires_at = expires_at or 0.0
        self.timeout = timeout
        self._transport = transport
        # Set True once we've rotated tokens, so callers can persist the new ones.
        self.refreshed = False

    @property
    def configured(self) -> bool:
        return bool(self.account_id and (self.access_token or self.can_refresh))

    @property
    def can_refresh(self) -> bool:
        return bool(self.client_id and self.client_secret and self.refresh_token)

    async def refresh(self) -> None:
        """Swap the refresh token for a fresh access token (and a NEW refresh token).

        Monzo ROTATES refresh tokens — the response carries a new one that
        replaces the old (now invalid) token, so the caller MUST persist it.
        """
        if not self.can_refresh:
            raise MonzoError("Cannot refresh: missing client_id / client_secret / refresh_token.")
        payload = await exchange_token(
            {
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
            },
            transport=self._transport,
        )
        self.access_token = payload["access_token"]
        self.refresh_token = payload.get("refresh_token", self.refresh_token)
        self.expires_at = time.time() + int(payload.get("expires_in", 0))
        self.refreshed = True

    async def _get(self, path: str, params: dict | None = None) -> dict:
        # Pre-emptively refresh when we know the token is (nearly) expired.
        if self.can_refresh and (not self.access_token or time.time() >= self.expires_at - 60):
            await self.refresh()

        resp = await self._raw_get(path, params)
        if resp.status_code == 401 and self.can_refresh:
            # Token rejected despite our clock — refresh once and retry.
            await self.refresh()
            resp = await self._raw_get(path, params)

        if resp.status_code == 401:
            raise MonzoError(
                "Monzo rejected the access token (401). Re-authorise with "
                "`python -m scripts.monzo_auth` (a refresh client won't need this again)."
            )
        if resp.status_code == 403:
            raise MonzoError(
                "Monzo returned 403. Approve API access in the Monzo app, then retry."
            )
        resp.raise_for_status()
        return resp.json()

    async def _raw_get(self, path: str, params: dict | None = None) -> httpx.Response:
        headers = {"Authorization": f"Bearer {self.access_token}"}
        async with httpx.AsyncClient(timeout=self.timeout, transport=self._transport) as client:
            return await client.get(f"{BASE_URL}{path}", headers=headers, params=params)

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
