from decimal import Decimal
from typing import Any

from .coinbase import CoinbaseClient, CoinbaseError

__all__ = ["CoinbaseClient", "CoinbaseError", "PROVIDER"]


async def _fetch_gbp(config: dict[str, Any]) -> Decimal:
    client = CoinbaseClient(
        api_key_name=config.get("api_key_name"),
        api_private_key=config.get("api_private_key"),
    )
    return await client.total_gbp()


# The plugin manifest core's registry discovers via the "finka.providers" entry
# point. Plain dict of built-in types only — this package never imports
# anything from core, so it can't break independently of it.
PROVIDER = {
    "key": "coinbase",
    "display_name": "Coinbase",
    "fetch": _fetch_gbp,
    "fields": [
        {"name": "api_key_name", "label": "API key name / id", "help": "CDP key id from portal.cdp.coinbase.com."},
        {"name": "api_private_key", "label": "Private key", "secret": True, "help": "The CDP private key (PEM or base64)."},
    ],
    "projection_fields": [
        {
            "name": "monthly_contribution", "label": "Monthly contribution", "required": False,
            "help": "Recurring amount you buy/deposit each month. Held flat in the projection if unset.",
        },
        {
            "name": "growth_rate", "label": "Expected annual return (%)", "required": False,
            "help": "Expected yearly return, as a percentage — e.g. 10 for 10%. Crypto is volatile — treat as a rough guess.",
            "placeholder": "10",
        },
    ],
}
