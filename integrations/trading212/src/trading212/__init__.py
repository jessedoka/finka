from decimal import Decimal
from typing import Any

from .trading212 import DEMO_BASE_URL, LIVE_BASE_URL, Trading212Client, Trading212Error

__all__ = ["Trading212Client", "Trading212Error", "LIVE_BASE_URL", "DEMO_BASE_URL", "PROVIDER"]


async def _fetch_gbp(config: dict[str, Any]) -> Decimal:
    base_url = DEMO_BASE_URL if config.get("demo") else LIVE_BASE_URL
    client = Trading212Client(api_key=config.get("api_key"), base_url=base_url)
    cash = await client.fetch_cash()
    return Decimal(str(cash["total"]))


# The plugin manifest core's registry discovers via the "finka.providers" entry
# point. Plain dict of built-in types only — this package never imports
# anything from core, so it can't break independently of it.
PROVIDER = {
    "key": "trading212",
    "display_name": "Trading212",
    "fetch": _fetch_gbp,
    "fields": [
        {
            "name": "api_key", "label": "API key", "secret": True,
            "help": "Settings → API (Beta). The raw key, no 'Bearer' prefix.",
        },
        {
            "name": "demo", "label": "Use demo host", "secret": False, "required": False,
            "help": "Set truthy if the key is for a demo account.",
        },
    ],
    "projection_fields": [
        {
            "name": "monthly_contribution", "label": "Monthly contribution", "required": False,
            "help": "Recurring amount you invest each month. Held flat in the projection if unset.",
        },
        {
            "name": "growth_rate", "label": "Expected annual return (%)", "required": False,
            "help": "Expected yearly return on this portfolio, as a percentage — e.g. 7 for 7%.",
            "placeholder": "7",
        },
    ],
}
