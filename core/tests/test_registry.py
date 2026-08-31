"""Registry: provider manifest, generic value-path extraction, validation."""

import pytest

from integrations import registry
from integrations.registry import ProviderError


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
