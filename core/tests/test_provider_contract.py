"""The provider contract — enforced against EVERY registered provider.

These tests are deliberately provider-agnostic: they parametrise over
`registry.list_specs()` rather than naming Monzo/Trading212/anything else. Add a
new provider and it is covered here automatically; break the contract and it
fails no matter which provider you broke.

The contract the rest of the app depends on:
  1. A spec's manifest is well-formed enough to render a form and validate input.
  2. `missing_required` reflects the declared required fields.
  3. `fetch_gbp` raises ONLY ProviderError — never a raw httpx/parse/native
     error. net_worth_service catches ProviderError alone, so a leak would let
     one broken source sink the whole snapshot.
  4. `fetch_gbp` returns a Decimal.
"""

from decimal import Decimal
from unittest.mock import patch

import httpx
import pytest

from integrations import registry
from integrations.registry import ProviderError, ProviderSpec

ALL_SPECS = registry.list_specs()
SPEC_IDS = [s.key for s in ALL_SPECS]

# A config carrying a plausible value for every field any provider declares, so
# each adapter gets far enough to attempt real work.
def _dummy_config(spec: ProviderSpec) -> dict:
    values = {
        "url": "https://provider.test/balance",
        "value_path": "balance",
        "method": "GET",
        "multiplier": 1,
    }
    return {name: values.get(name, "dummy-value") for name in spec.field_names()}


@pytest.mark.parametrize("spec", ALL_SPECS, ids=SPEC_IDS)
def test_manifest_is_well_formed(spec: ProviderSpec):
    assert spec.key and spec.display_name
    assert spec.fields, "a provider must declare at least one config field"

    names = [f.name for f in spec.fields]
    assert len(names) == len(set(names)), "duplicate field names"
    for f in spec.fields:
        assert f.name and f.label, f"field {f.name!r} needs a name and a label"

    # Secrets must be a subset of declared fields, or redaction would miss them.
    assert spec.secret_names() <= set(names)


@pytest.mark.parametrize("spec", ALL_SPECS, ids=SPEC_IDS)
def test_missing_required_matches_declared_required_fields(spec: ProviderSpec):
    required = {f.name for f in spec.fields if f.required}
    # Empty config: every required field is reported missing.
    assert set(spec.missing_required({})) == required
    # Fully populated config: nothing missing.
    assert spec.missing_required(_dummy_config(spec)) == []


@pytest.mark.parametrize("spec", ALL_SPECS, ids=SPEC_IDS)
@pytest.mark.asyncio
async def test_empty_config_raises_provider_error(spec: ProviderSpec):
    """A blank/never-configured source must fail cleanly, not explode."""
    with pytest.raises(ProviderError):
        await spec.fetch_gbp({})


@pytest.mark.parametrize("spec", ALL_SPECS, ids=SPEC_IDS)
@pytest.mark.asyncio
async def test_network_failure_normalises_to_provider_error(spec: ProviderSpec):
    """The resilience guarantee: a network blip can't sink the snapshot.

    Without this, a raw httpx error escapes _collect_balances (which catches
    ProviderError only) and takes every OTHER source down with it.
    """

    async def unreachable(*args, **kwargs):
        raise httpx.ConnectError("network down")

    with (
        patch.object(httpx.AsyncClient, "send", unreachable),
        patch.object(httpx.AsyncClient, "request", unreachable),
    ):
        with pytest.raises(ProviderError):
            await spec.fetch_gbp(_dummy_config(spec))


@pytest.mark.parametrize("spec", ALL_SPECS, ids=SPEC_IDS)
@pytest.mark.asyncio
async def test_garbage_response_normalises_to_provider_error(spec: ProviderSpec):
    """Non-JSON / unexpected payloads are a provider problem, not a crash."""

    async def garbage(*args, **kwargs):
        return httpx.Response(200, text="<html>not json</html>")

    with (
        patch.object(httpx.AsyncClient, "send", garbage),
        patch.object(httpx.AsyncClient, "request", garbage),
    ):
        with pytest.raises(ProviderError):
            await spec.fetch_gbp(_dummy_config(spec))


@pytest.mark.asyncio
async def test_fetch_gbp_returns_decimal():
    """Whatever an adapter hands back is coerced to Decimal for the aggregator."""

    async def returns_float(_config):
        return 12.5

    spec = ProviderSpec(
        key="stub", display_name="Stub", fetch=returns_float, fields=[]
    )
    value = await spec.fetch_gbp({})
    assert value == Decimal("12.5")
    assert isinstance(value, Decimal)


@pytest.mark.asyncio
async def test_non_numeric_value_raises_provider_error():
    async def returns_junk(_config):
        return "not-a-number"

    spec = ProviderSpec(key="stub", display_name="Stub", fetch=returns_junk, fields=[])
    with pytest.raises(ProviderError):
        await spec.fetch_gbp({})
