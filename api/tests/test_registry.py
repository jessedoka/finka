"""Registry: provider manifest, generic value-path extraction, validation."""

import pytest

from integrations import registry
from integrations.registry import ProviderError, _extract


def test_all_providers_registered():
    keys = {s.key for s in registry.list_specs()}
    assert keys == {"monzo", "trading212", "coinbase", "http"}


def test_get_unknown_provider_raises():
    with pytest.raises(ProviderError):
        registry.get("nope")


def test_missing_required_flags_empty_fields():
    spec = registry.get("monzo")
    # account_id is the only required field — tokens are set by the OAuth helper,
    # so access_token / client creds are optional.
    assert set(spec.missing_required({})) == {"account_id"}
    # optional (OAuth / projection) fields never count as missing
    assert spec.missing_required({"account_id": "a"}) == []


def test_http_optional_fields_not_required():
    spec = registry.get("http")
    # url + value_path required; method/headers/multiplier optional
    assert set(spec.missing_required({})) == {"url", "value_path"}


@pytest.mark.parametrize(
    "payload,path,expected",
    [
        ({"balance": 1234}, "balance", 1234),
        ({"data": {"balance": {"amount": "50.5"}}}, "data.balance.amount", "50.5"),
        ({"accounts": [{"balance": 10}, {"balance": 20}]}, "accounts.1.balance", 20),
        ({"balance": 5}, "", {"balance": 5}),  # empty path returns whole payload
    ],
)
def test_extract_walks_path(payload, path, expected):
    assert _extract(payload, path) == expected


@pytest.mark.parametrize(
    "payload,path",
    [
        ({"balance": 1}, "missing"),
        ({"items": [1]}, "items.5"),
        ({"balance": 1}, "balance.deeper"),  # can't index into an int
    ],
)
def test_extract_bad_path_raises(payload, path):
    with pytest.raises(ProviderError):
        _extract(payload, path)
