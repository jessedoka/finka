"""The generic HTTP connector — the bring-your-own-source path.

This is the connector that isn't tied to any particular provider, so it carries
the most weight for a consumer wiring up their own endpoint. Covers request
shaping (method, headers), value extraction, the multiplier, and the failure
modes a user is most likely to hit while setting one up.
"""

from decimal import Decimal
from unittest.mock import patch

import httpx
import pytest

from integrations import registry
from integrations.registry import ProviderError

SPEC = registry.get("http")


def _responder(response: httpx.Response, seen: dict | None = None):
    """Patch-in for AsyncClient.request that records the outgoing call."""

    async def _request(self, method, url, *args, **kwargs):
        if seen is not None:
            seen["method"] = method
            seen["url"] = url
            seen["headers"] = kwargs.get("headers")
        # raise_for_status() needs the originating request attached.
        response.request = httpx.Request(method, url)
        return response

    return _request


async def _fetch(config: dict, response: httpx.Response, seen: dict | None = None) -> Decimal:
    with patch.object(httpx.AsyncClient, "request", _responder(response, seen)):
        return await SPEC.fetch_gbp(config)


@pytest.mark.asyncio
async def test_extracts_nested_value_and_sends_auth_headers():
    seen: dict = {}
    body = {"status": "ok", "data": {"balance": {"amount": "12345.67"}}}
    value = await _fetch(
        {
            "url": "https://provider.test/v1/account",
            "value_path": "data.balance.amount",
            "headers": {"Authorization": "Bearer tkn"},
        },
        httpx.Response(200, json=body),
        seen,
    )

    assert value == Decimal("12345.67")
    assert seen["method"] == "GET"  # default
    assert seen["url"] == "https://provider.test/v1/account"
    assert seen["headers"]["Authorization"] == "Bearer tkn"


@pytest.mark.asyncio
async def test_multiplier_converts_minor_units():
    """The documented way to turn pennies into pounds."""
    value = await _fetch(
        {"url": "https://x.test", "value_path": "balance", "multiplier": "0.01"},
        httpx.Response(200, json={"balance": 500000}),
    )
    assert value == Decimal("5000.00")


@pytest.mark.asyncio
async def test_indexes_into_arrays():
    value = await _fetch(
        {"url": "https://x.test", "value_path": "accounts.1.balance"},
        httpx.Response(200, json={"accounts": [{"balance": 10}, {"balance": 20}]}),
    )
    assert value == Decimal("20")


@pytest.mark.asyncio
async def test_custom_method_is_used():
    seen: dict = {}
    await _fetch(
        {"url": "https://x.test", "value_path": "balance", "method": "post"},
        httpx.Response(200, json={"balance": 1}),
        seen,
    )
    assert seen["method"] == "POST"  # upper-cased


@pytest.mark.asyncio
async def test_missing_url_is_rejected():
    with pytest.raises(ProviderError, match="url"):
        await SPEC.fetch_gbp({"value_path": "balance"})


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "config,response,reason",
    [
        (
            {"url": "https://x.test", "value_path": "nope"},
            httpx.Response(200, json={"balance": 1}),
            "path not in payload",
        ),
        (
            {"url": "https://x.test", "value_path": "balance"},
            httpx.Response(200, text="<html>login</html>"),
            "not JSON",
        ),
        (
            {"url": "https://x.test", "value_path": "balance"},
            httpx.Response(401, json={"error": "unauthorized"}),
            "auth rejected",
        ),
        (
            {"url": "https://x.test", "value_path": "name"},
            httpx.Response(200, json={"name": "Current Account"}),
            "value is not numeric",
        ),
    ],
)
async def test_setup_mistakes_surface_as_provider_errors(config, response, reason):
    """Each of these is a mistake a user makes while configuring a source; all
    must come back as a clean, explainable ProviderError."""
    with pytest.raises(ProviderError):
        await _fetch(config, response)
