"""Tests for the mechanical T212 client: auth header, parsing, 429 backoff.

Uses httpx.MockTransport so no real network / no real key is needed.
"""

import httpx
import pytest

from integrations.trading212 import Trading212Client, Trading212Error


@pytest.mark.asyncio
async def test_fetch_cash_sends_key_and_parses():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("Authorization")
        seen["url"] = str(request.url)
        return httpx.Response(200, json={"free": 10.0, "invested": 90.0, "total": 100.0})

    client = Trading212Client("my-secret-key", transport=httpx.MockTransport(handler))
    cash = await client.fetch_cash()

    assert cash["total"] == 100.0
    # raw key, NOT "Bearer ..."
    assert seen["auth"] == "my-secret-key"
    assert seen["url"].endswith("/api/v0/equity/account/cash")


@pytest.mark.asyncio
async def test_retries_on_429_then_succeeds(monkeypatch):
    # don't actually sleep during the backoff
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
async def test_bad_key_raises(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401)

    client = Trading212Client("wrong", transport=httpx.MockTransport(handler))
    with pytest.raises(Trading212Error):
        await client.fetch_cash()
