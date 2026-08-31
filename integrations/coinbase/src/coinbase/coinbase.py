"""Coinbase read-only client (MECHANICAL / plumbing only).

Talks HTTP to Coinbase and hands back raw JSON / a GBP total. Knows nothing
about Finka's models or DB — aggregation lives in services/net_worth_service.py.

AUTH: Coinbase Developer Platform (CDP) API keys. A key is an id/name plus a
private key; every request carries a short-lived JWT signed with it
(Authorization: Bearer <jwt>). Two key formats exist and we support both:
  - Ed25519 (current default): id is a UUID, secret is base64 -> signed EdDSA.
  - ECDSA (older): secret is a PEM ("BEGIN EC PRIVATE KEY") -> signed ES256.
Create one with "View" permission only at https://portal.cdp.coinbase.com/.

VALUATION: balances come back in their own asset (BTC, ETH, GBP, ...). We value
each in GBP via Coinbase's PUBLIC spot-price endpoint (no auth). Fiat balances
already in GBP are taken at face value.

Credentials come from the user's Coinbase Connection, not config — use the
"Test" action on the Connections page to confirm a key works.
"""

import base64
import logging
import secrets
import time
from decimal import Decimal

import httpx
import jwt
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


logger = logging.getLogger(__name__)

API_HOST = "api.coinbase.com"
BASE_URL = f"https://{API_HOST}"


class CoinbaseError(RuntimeError):
    """Raised when the Coinbase API returns an unrecoverable error."""


class CoinbaseClient:
    def __init__(
        self,
        api_key_name: str | None = None,
        api_private_key: str | None = None,
        *,
        timeout: float = 15.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.api_key_name = api_key_name or ""
        # A PEM pasted into a single line carries escaped newlines; restore them.
        self.api_private_key = (api_private_key or "").replace("\\n", "\n")
        self.timeout = timeout
        self._transport = transport

    @property
    def configured(self) -> bool:
        return bool(self.api_key_name and self.api_private_key)

    def _signing_material(self):
        """Return (key, algorithm) for jwt.encode, picking format by key shape."""
        key = self.api_private_key.strip()
        if key.startswith("-----BEGIN"):
            return key, "ES256"  # ECDSA PEM
        # Otherwise a base64 Ed25519 secret: 64 bytes = 32 seed + 32 public.
        try:
            raw = base64.b64decode(key)
            private_key = Ed25519PrivateKey.from_private_bytes(raw[:32])
        except Exception as e:
            raise CoinbaseError(f"Malformed Coinbase private key: {e}") from e
        return private_key, "EdDSA"

    def _jwt(self, method: str, path: str) -> str:
        """A 2-minute JWT bound to this exact METHOD + host + path."""
        now = int(time.time())
        # `path` may carry a query string; the signed uri claim uses path only.
        clean_path = path.split("?", 1)[0]
        payload = {
            "sub": self.api_key_name,
            "iss": "cdp",
            "nbf": now,
            "exp": now + 120,
            "uri": f"{method} {API_HOST}{clean_path}",
        }
        headers = {"kid": self.api_key_name, "nonce": secrets.token_hex(16)}
        try:
            key, alg = self._signing_material()
            return jwt.encode(payload, key, algorithm=alg, headers=headers)
        except CoinbaseError:
            raise
        except Exception as e:  # bad/malformed key material
            raise CoinbaseError(f"Could not sign Coinbase JWT: {e}") from e

    async def _get(self, client: httpx.AsyncClient, path: str, *, auth: bool, params: dict | None = None) -> dict:
        headers = {"Authorization": f"Bearer {self._jwt('GET', path)}"} if auth else {}
        resp = await client.get(f"{BASE_URL}{path}", headers=headers, params=params)
        if resp.status_code == 401:
            raise CoinbaseError("Coinbase rejected the API key (401). Check the key name and PEM.")
        resp.raise_for_status()
        return resp.json()

    async def fetch_accounts(self) -> list[dict]:
        """All wallet accounts (paginated), each with a `balance` {amount,currency}."""
        accounts: list[dict] = []
        path = "/v2/accounts?limit=100"
        async with httpx.AsyncClient(timeout=self.timeout, transport=self._transport) as client:
            while path:
                body = await self._get(client, path, auth=True)
                accounts.extend(body.get("data", []))
                # v2 pagination: pagination.next_uri is a full path or null.
                path = (body.get("pagination") or {}).get("next_uri") or ""
        return accounts

    async def _spot_gbp(self, client: httpx.AsyncClient, base: str, cache: dict[str, Decimal]) -> Decimal:
        """GBP price of one unit of `base` via the public spot endpoint."""
        if base == "GBP":
            return Decimal("1")
        if base in cache:
            return cache[base]
        try:
            body = await self._get(client, f"/v2/prices/{base}-GBP/spot", auth=False)
            price = Decimal(str(body["data"]["amount"]))
        except (httpx.HTTPStatusError, KeyError):
            logger.warning("No GBP spot price for %s; valuing it at 0", base)
            price = Decimal("0")
        cache[base] = price
        return price

    async def total_gbp(self) -> Decimal:
        """Sum of every account balance valued in GBP."""
        accounts = await self.fetch_accounts()
        total = Decimal("0")
        cache: dict[str, Decimal] = {}
        async with httpx.AsyncClient(timeout=self.timeout, transport=self._transport) as client:
            for acct in accounts:
                bal = acct.get("balance") or {}
                amount = Decimal(str(bal.get("amount", "0")))
                if amount == 0:
                    continue
                total += amount * await self._spot_gbp(client, bal.get("currency", "GBP"), cache)
        return total
