"""Provider registry — the plugin seam for "bring your own source".

A *provider* is a kind of data source (Monzo, Trading212, Coinbase, or a
generic pollable HTTP endpoint). A user's `Connection` row picks a provider by
key and supplies its `config` (credentials + settings). This registry maps a
provider key + config onto a single GBP figure, so the service layer never
names a provider — it just loops over the user's connections.

Adding a named provider = registering one more `ProviderSpec` here (reusing the
mechanical client in this package). Everything else — the API, the frontend
form, the net-worth aggregation — is driven off `fields` and needs no change.

Each spec's `fields` describes the config schema: it drives both the dynamic
frontend form and connect-time validation. `secret` fields are write-only —
their values are never returned on reads.
"""

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Awaitable, Callable

import httpx

from integrations.coinbase import CoinbaseClient, CoinbaseError
from integrations.monzo import MonzoClient, MonzoError
from integrations.trading212 import LIVE_BASE_URL, DEMO_BASE_URL, Trading212Client, Trading212Error

logger = logging.getLogger(__name__)


class ProviderError(RuntimeError):
    """Raised when a provider can't produce a balance from its config."""


@dataclass(frozen=True)
class ProviderField:
    name: str
    label: str
    secret: bool = False
    required: bool = True
    help: str = ""
    placeholder: str = ""


@dataclass(frozen=True)
class ProviderSpec:
    key: str
    display_name: str
    fields: list[ProviderField]
    # The raw adapter. Call `fetch_gbp()` instead — it enforces the contract.
    fetch: Callable[[dict[str, Any]], Awaitable[Any]]
    # Optional projection knobs a connection may set in its config; listed so the
    # projection service and the UI know which extra keys are meaningful.
    projection_fields: list[ProviderField] = field(default_factory=list)

    async def fetch_gbp(self, config: dict[str, Any]) -> Decimal:
        """Fetch this source's value as a Decimal, normalising ALL failures.

        The contract every caller relies on: this raises `ProviderError` and
        nothing else. Aggregation (net_worth_service) catches only ProviderError
        so one broken source contributes 0 instead of sinking the whole
        snapshot — a provider leaking a raw httpx/parse error would defeat that.
        Enforced here, centrally, so a new provider can't forget it.
        """
        try:
            value = await self.fetch(config or {})
        except ProviderError:
            raise
        except Exception as e:  # network, auth, parsing, provider-native errors
            raise ProviderError(f"{self.display_name}: {e}") from e
        try:
            return Decimal(str(value))
        except Exception as e:
            raise ProviderError(f"{self.display_name} returned a non-numeric value: {value!r}") from e

    def field_names(self) -> set[str]:
        return {f.name for f in self.fields} | {f.name for f in self.projection_fields}

    def secret_names(self) -> set[str]:
        return {f.name for f in self.fields if f.secret}

    def missing_required(self, config: dict[str, Any]) -> list[str]:
        return [f.name for f in self.fields if f.required and not config.get(f.name)]


# --- named providers: thin adapters over the existing mechanical clients ------


async def _monzo_gbp(config: dict[str, Any]) -> Decimal:
    client = MonzoClient(
        access_token=config.get("access_token"),
        account_id=config.get("account_id"),
        client_id=config.get("client_id"),
        client_secret=config.get("client_secret"),
        refresh_token=config.get("refresh_token"),
        expires_at=config.get("monzo_expires_at"),
    )
    try:
        value = await client.total_gbp()
    except MonzoError as e:
        raise ProviderError(str(e)) from e
    # If the OAuth token rotated mid-fetch, write the new tokens back into the
    # SAME config dict. net_worth_service flags the connection's config modified
    # so these persist — otherwise the rotated refresh token is lost and the next
    # refresh fails. This is what makes the connection permanent (no re-pasting).
    if client.refreshed:
        config["access_token"] = client.access_token
        config["refresh_token"] = client.refresh_token
        config["monzo_expires_at"] = client.expires_at
    return value


async def _trading212_gbp(config: dict[str, Any]) -> Decimal:
    base_url = DEMO_BASE_URL if config.get("demo") else LIVE_BASE_URL
    client = Trading212Client(api_key=config.get("api_key"), base_url=base_url)
    try:
        cash = await client.fetch_cash()
        return Decimal(str(cash["total"]))
    except (Trading212Error, KeyError) as e:
        raise ProviderError(f"Trading212 balance unavailable: {e}") from e


async def _coinbase_gbp(config: dict[str, Any]) -> Decimal:
    client = CoinbaseClient(
        api_key_name=config.get("api_key_name"),
        api_private_key=config.get("api_private_key"),
    )
    try:
        return await client.total_gbp()
    except CoinbaseError as e:
        raise ProviderError(str(e)) from e


# --- generic HTTP connector: any pollable endpoint that returns a number ------


def _extract(payload: Any, path: str) -> Any:
    """Walk a dotted/indexed path into JSON (e.g. "data.accounts.0.balance")."""
    current = payload
    for part in path.split("."):
        if part == "":
            continue
        if isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError) as e:
                raise ProviderError(f"value_path segment '{part}' not found in list") from e
        elif isinstance(current, dict):
            if part not in current:
                raise ProviderError(f"value_path segment '{part}' not found in response")
            current = current[part]
        else:
            raise ProviderError(f"value_path segment '{part}' can't index a {type(current).__name__}")
    return current


async def _http_gbp(config: dict[str, Any]) -> Decimal:
    url = config.get("url")
    if not url:
        raise ProviderError("Generic HTTP connector needs a url")
    method = (config.get("method") or "GET").upper()
    headers = config.get("headers") or {}
    value_path = config.get("value_path") or ""
    try:
        multiplier = Decimal(str(config.get("multiplier", 1)))
    except Exception as e:
        raise ProviderError(f"multiplier must be a number: {e}") from e

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.request(method, url, headers=headers)
        resp.raise_for_status()
        payload = resp.json()
    except httpx.HTTPError as e:
        raise ProviderError(f"HTTP request failed: {e}") from e
    except ValueError as e:
        raise ProviderError(f"Response was not JSON: {e}") from e

    raw = _extract(payload, value_path)
    try:
        return Decimal(str(raw)) * multiplier
    except Exception as e:
        raise ProviderError(f"Extracted value '{raw}' is not a number: {e}") from e


_SPECS: dict[str, ProviderSpec] = {
    "monzo": ProviderSpec(
        key="monzo",
        display_name="Monzo",
        fetch=_monzo_gbp,
        fields=[
            ProviderField("account_id", "Account ID", help="The Monzo account to read."),
            ProviderField(
                "access_token", "Access token", secret=True, required=False,
                help="Set by `python -m scripts.monzo_auth`; auto-refreshed thereafter. "
                "A short-lived playground token also works but will expire.",
            ),
            # OAuth confidential-client credentials — presence enables permanent,
            # self-refreshing access. Populated by scripts.monzo_auth.
            ProviderField("client_id", "OAuth client ID", required=False,
                          help="oauth2client_… from developers.monzo.com (Confidential client)."),
            ProviderField("client_secret", "OAuth client secret", secret=True, required=False,
                          help="mnzconf… from the same client."),
            ProviderField("refresh_token", "OAuth refresh token", secret=True, required=False,
                          help="Obtained + rotated automatically; do not set by hand."),
            ProviderField("monzo_expires_at", "Access-token expiry (epoch)", required=False,
                          help="Managed automatically."),
        ],
        projection_fields=[
            ProviderField("monthly_contribution", "Monthly contribution", required=False),
            ProviderField("growth_rate", "Annual growth rate (e.g. 0.02)", required=False),
        ],
    ),
    "trading212": ProviderSpec(
        key="trading212",
        display_name="Trading212",
        fetch=_trading212_gbp,
        fields=[
            ProviderField(
                "api_key", "API key", secret=True,
                help="Settings → API (Beta). The raw key, no 'Bearer' prefix.",
            ),
            ProviderField(
                "demo", "Use demo host", secret=False, required=False,
                help="Set truthy if the key is for a demo account.",
            ),
        ],
    ),
    "coinbase": ProviderSpec(
        key="coinbase",
        display_name="Coinbase",
        fetch=_coinbase_gbp,
        fields=[
            ProviderField("api_key_name", "API key name / id", help="CDP key id from portal.cdp.coinbase.com."),
            ProviderField("api_private_key", "Private key", secret=True, help="The CDP private key (PEM or base64)."),
        ],
    ),
    "http": ProviderSpec(
        key="http",
        display_name="Generic HTTP (JSON)",
        fetch=_http_gbp,
        fields=[
            ProviderField("url", "URL", help="An endpoint returning JSON with a balance."),
            ProviderField(
                "value_path", "Value path",
                help="Dotted path to the number, e.g. data.balance.amount or accounts.0.balance.",
                placeholder="data.balance",
            ),
            ProviderField(
                "method", "HTTP method", required=False, help="GET (default) or POST.",
                placeholder="GET",
            ),
            ProviderField(
                "headers", "Headers (JSON object)", secret=True, required=False,
                help='Auth headers, e.g. {"Authorization": "Bearer …"}. Stored as-is.',
            ),
            ProviderField(
                "multiplier", "Multiplier", required=False,
                help="Scales the value — e.g. 0.01 to convert pennies to pounds. Also use to pre-convert currency (no FX built in).",
                placeholder="1",
            ),
        ],
    ),
}


def list_specs() -> list[ProviderSpec]:
    return list(_SPECS.values())


def get(key: str) -> ProviderSpec:
    spec = _SPECS.get(key)
    if spec is None:
        raise ProviderError(f"Unknown provider '{key}'")
    return spec
