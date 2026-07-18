"""Trading212 public API client (MECHANICAL / plumbing only).

This module's ONLY job is to talk HTTP to Trading212 and hand back the raw
JSON dicts. It deliberately knows nothing about Finka's models, database, or
users. Mapping T212's shape onto Account / NetWorthSnapshot is the service
layer's job (services/trading212_service.py) — that's the part you write.

NOTE ON ENDPOINTS: the T212 docs sit behind a login, so the paths below are my
best knowledge of the v0 API. Verify them against your own account's docs
(Settings -> API (Beta)); if a path 404s, that's the first thing to check.

Auth: T212 expects the raw API key in the `Authorization` header — NOT
`Bearer <key>`, just the key itself.

Rate limits are strict and per-endpoint (cash ~1 req / 2s, portfolio slower,
metadata much slower). We do a light exponential backoff on HTTP 429 rather
than pull in a retry dependency.
"""

import asyncio
import logging

import httpx

from config import settings

logger = logging.getLogger(__name__)

# Live vs demo are DIFFERENT hosts. A key generated on your real account only
# works against the live host.
LIVE_BASE_URL = "https://live.trading212.com"
DEMO_BASE_URL = "https://demo.trading212.com"

API_PREFIX = "/api/v0"


class Trading212Error(RuntimeError):
    """Raised when the T212 API returns an unrecoverable error."""


class Trading212Client:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = LIVE_BASE_URL,
        timeout: float = 15.0,
        max_retries: int = 4,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.api_key = api_key or settings.trading_212_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        # Injectable purely so tests can feed a mock transport; None => real net.
        self._transport = transport

    def _headers(self) -> dict[str, str]:
        return {"Authorization": self.api_key}

    async def _get(self, path: str, params: dict | None = None) -> dict | list:
        """GET {base}{API_PREFIX}{path} with auth + backoff on 429."""
        url = f"{self.base_url}{API_PREFIX}{path}"
        delay = 2.0

        async with httpx.AsyncClient(timeout=self.timeout, transport=self._transport) as client:
            for attempt in range(1, self.max_retries + 1):
                resp = await client.get(url, headers=self._headers(), params=params)

                if resp.status_code == 429:
                    if attempt == self.max_retries:
                        raise Trading212Error(
                            f"Rate limited by T212 on {path} after {attempt} attempts"
                        )
                    logger.warning(
                        "T212 rate limited %s (attempt %d/%d); backing off %.1fs",
                        path, attempt, self.max_retries, delay,
                    )
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue

                if resp.status_code == 401:
                    raise Trading212Error(
                        "T212 rejected the API key (401). Check the key and "
                        "that it matches the host (live vs demo)."
                    )

                resp.raise_for_status()
                return resp.json()

        raise Trading212Error(f"Exhausted retries fetching {path}")

    # --- raw fetchers: one per endpoint, each returns T212's JSON verbatim ---

    async def fetch_cash(self) -> dict:
        """Account cash summary: free, invested, ppl, total, etc."""
        return await self._get("/equity/account/cash")  # type: ignore[return-value]

    async def fetch_account_info(self) -> dict:
        """Account metadata: id, currencyCode."""
        return await self._get("/equity/account/info")  # type: ignore[return-value]

    async def fetch_portfolio(self) -> list:
        """Open positions: list of {ticker, quantity, currentPrice, ppl, ...}."""
        return await self._get("/equity/portfolio")  # type: ignore[return-value]

    async def fetch_order_history(self, *, cursor: int | None = None, limit: int = 50) -> dict:
        """Historical orders (paginated). `items` + `nextPagePath` in response."""
        params: dict = {"limit": limit}
        if cursor is not None:
            params["cursor"] = cursor
        return await self._get("/equity/history/orders", params=params)  # type: ignore[return-value]
