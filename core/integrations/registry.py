import logging
from decimal import Decimal
from typing import Any 

from integrations.contract import ProviderSpec, ProviderField, ProviderError
from http_connector import http_gbp

from integrations.coinbase import CoinbaseClient, CoinbaseError
from integrations.monzo import MonzoClient, MonzoError
from integrations.trading212 import LIVE_BASE_URL, DEMO_BASE_URL, Trading212Client, Trading212Error

logger = logging.getLogger(__name__)

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
            ProviderField(
                "monthly_contribution", "Monthly contribution", required=False,
                help="Recurring amount you add each month (e.g. savings pot top-ups). Held flat in the projection if unset.",
            ),
            ProviderField(
                "growth_rate", "Interest rate (%)", required=False,
                help="Interest this pot earns per year, as a percentage — e.g. 3.25 for a 3.25% AER.",
                placeholder="3.25",
            ),
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
        projection_fields=[
            ProviderField(
                "monthly_contribution", "Monthly contribution", required=False,
                help="Recurring amount you invest each month. Held flat in the projection if unset.",
            ),
            ProviderField(
                "growth_rate", "Expected annual return (%)", required=False,
                help="Expected yearly return on this portfolio, as a percentage — e.g. 7 for 7%.",
                placeholder="7",
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
        projection_fields=[
            ProviderField(
                "monthly_contribution", "Monthly contribution", required=False,
                help="Recurring amount you buy/deposit each month. Held flat in the projection if unset.",
            ),
            ProviderField(
                "growth_rate", "Expected annual return (%)", required=False,
                help="Expected yearly return, as a percentage — e.g. 10 for 10%. Crypto is volatile — treat as a rough guess.",
                placeholder="10",
            ),
        ],
    ),
    "http": ProviderSpec(
        key="http",
        display_name="Generic HTTP (JSON)",
        fetch=http_gbp,
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
        projection_fields=[
            ProviderField(
                "monthly_contribution", "Monthly contribution", required=False,
                help="Recurring amount added each month. Held flat in the projection if unset.",
            ),
            ProviderField(
                "growth_rate", "Annual growth rate (%)", required=False,
                help="Expected yearly growth, as a percentage — e.g. 5 for 5%.",
                placeholder="5",
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
