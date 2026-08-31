from decimal import Decimal
from typing import Any

from .monzo import AUTH_URL, TOKEN_URL, MonzoClient, MonzoError, exchange_token

__all__ = ["MonzoClient", "MonzoError", "exchange_token", "AUTH_URL", "TOKEN_URL", "PROVIDER"]


async def _fetch_gbp(config: dict[str, Any]) -> Decimal:
    client = MonzoClient(
        access_token=config.get("access_token"),
        account_id=config.get("account_id"),
        client_id=config.get("client_id"),
        client_secret=config.get("client_secret"),
        refresh_token=config.get("refresh_token"),
        expires_at=config.get("monzo_expires_at"),
    )
    value = await client.total_gbp()
    # If the OAuth token rotated mid-fetch, write the new tokens back into the
    # SAME config dict. net_worth_service flags the connection's config modified
    # so these persist — otherwise the rotated refresh token is lost and the
    # next refresh fails. This is what makes the connection permanent.
    if client.refreshed:
        config["access_token"] = client.access_token
        config["refresh_token"] = client.refresh_token
        config["monzo_expires_at"] = client.expires_at
    return value


# The plugin manifest core's registry discovers via the "finka.providers" entry
# point. Plain dict of built-in types only — this package never imports
# anything from core, so it can't break independently of it.
PROVIDER = {
    "key": "monzo",
    "display_name": "Monzo",
    "fetch": _fetch_gbp,
    "fields": [
        {"name": "account_id", "label": "Account ID", "help": "The Monzo account to read."},
        {
            "name": "access_token", "label": "Access token", "secret": True, "required": False,
            "help": "Set by `python -m scripts.monzo_auth`; auto-refreshed thereafter. "
            "A short-lived playground token also works but will expire.",
        },
        {
            "name": "client_id", "label": "OAuth client ID", "required": False,
            "help": "oauth2client_… from developers.monzo.com (Confidential client).",
        },
        {
            "name": "client_secret", "label": "OAuth client secret", "secret": True, "required": False,
            "help": "mnzconf… from the same client.",
        },
        {
            "name": "refresh_token", "label": "OAuth refresh token", "secret": True, "required": False,
            "help": "Obtained + rotated automatically; do not set by hand.",
        },
        {
            "name": "monzo_expires_at", "label": "Access-token expiry (epoch)", "required": False,
            "help": "Managed automatically.",
        },
    ],
    "projection_fields": [
        {
            "name": "monthly_contribution", "label": "Monthly contribution", "required": False,
            "help": "Recurring amount you add each month (e.g. savings pot top-ups). Held flat in the projection if unset.",
        },
        {
            "name": "growth_rate", "label": "Interest rate (%)", "required": False,
            "help": "Interest this pot earns per year, as a percentage — e.g. 3.25 for a 3.25% AER.",
            "placeholder": "3.25",
        },
    ],
}
