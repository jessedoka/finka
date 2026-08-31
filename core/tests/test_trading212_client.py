"""Trading212 client: the rate-limit backoff loop.

Kept deliberately narrow. The provider-agnostic guarantees — auth reaching the
wire, errors normalising to ProviderError, Decimal in/out — are covered for
EVERY provider in test_provider_contract.py; duplicating them per provider just
anchors the suite to whichever integrations happen to exist today.

What survives here is the one piece of genuinely non-trivial mechanical logic
that no other provider shares: T212's strict per-endpoint rate limits mean this
client retries with exponential backoff, and that loop is worth pinning down.
"""

import httpx
import pytest

from integrations.trading212 import Trading212Client, Trading212Error


@pytest.mark.asyncio
async def test_retries_on_429_then_succeeds(monkeypatch):
    # Don't actually sleep through the backoff.
    async def no_sleep(_):
        return None

    monkeypatch.setattr("integrations.trading212.asyncio.sleep", no_sleep)

    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429)
        return httpx.Response(200, json=[{"ticker": "AAPL", "quantity": 3}])

    client = Trading212Client("k", transport=httpx.MockTransport(handler))
    portfolio = await client.fetch_portfolio()

    assert calls["n"] == 2
    assert portfolio[0]["ticker"] == "AAPL"


@pytest.mark.asyncio
async def test_gives_up_after_max_retries(monkeypatch):
    async def no_sleep(_):
        return None

    monkeypatch.setattr("integrations.trading212.asyncio.sleep", no_sleep)

    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(429)

    client = Trading212Client("k", max_retries=3, transport=httpx.MockTransport(handler))
    with pytest.raises(Trading212Error):
        await client.fetch_cash()

    assert calls["n"] == 3
