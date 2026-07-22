"""Monzo client: the OAuth auto-refresh + token rotation.

The provider-agnostic guarantees are covered in test_provider_contract.py. What's
unique to Monzo and worth pinning: a confidential client refreshes an expired /
rejected access token on the fly, and MUST surface the ROTATED refresh token so
the caller can persist it (that's what makes the connection permanent).
"""

import time

import httpx
import pytest

from integrations.monzo import MonzoClient


def _handler(state):
    """Mock transport: /oauth2/token rotates creds; /balance needs the new token."""
    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth2/token":
            state["token_calls"] += 1
            return httpx.Response(200, json={
                "access_token": "new_at",
                "refresh_token": "rotated_rt",
                "expires_in": 21600,
            })
        # /balance: only the freshly refreshed token is accepted.
        if request.headers.get("Authorization") == "Bearer new_at":
            return httpx.Response(200, json={"balance": 1000, "total_balance": 5000})
        return httpx.Response(401)
    return handle


@pytest.mark.asyncio
async def test_expired_token_is_refreshed_preemptively():
    state = {"token_calls": 0}
    client = MonzoClient(
        access_token="old_at", account_id="acc", client_id="cid",
        client_secret="sec", refresh_token="old_rt",
        expires_at=time.time() - 10,  # already expired
        transport=httpx.MockTransport(_handler(state)),
    )
    value = await client.total_gbp()

    assert value == pytest.approx(40)          # (5000 - 1000) minor / 100
    assert state["token_calls"] == 1           # refreshed exactly once
    assert client.refreshed is True
    assert client.refresh_token == "rotated_rt"  # rotation surfaced for persisting


@pytest.mark.asyncio
async def test_401_triggers_refresh_and_retry():
    state = {"token_calls": 0}
    client = MonzoClient(
        access_token="old_at", account_id="acc", client_id="cid",
        client_secret="sec", refresh_token="old_rt",
        expires_at=time.time() + 3600,  # looks valid, but server rejects it
        transport=httpx.MockTransport(_handler(state)),
    )
    value = await client.total_gbp()

    assert value == pytest.approx(40)
    assert state["token_calls"] == 1
    assert client.access_token == "new_at"


@pytest.mark.asyncio
async def test_no_refresh_creds_still_raises_on_401():
    def handle(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401)

    client = MonzoClient(
        access_token="stale", account_id="acc",
        transport=httpx.MockTransport(handle),
    )
    with pytest.raises(Exception):  # MonzoError — no way to refresh
        await client.total_gbp()
    assert client.refreshed is False
