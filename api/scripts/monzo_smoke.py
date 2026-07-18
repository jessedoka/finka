"""Throwaway smoke test: prove the Monzo connection works, print the balance.

Run AFTER putting your playground token in the root .env (MONZO_ACCESS_TOKEN +
MONZO_ACCOUNT_ID):

    .venv/bin/python -m scripts.monzo_smoke

Does NOT touch the database. Delete once you trust the integration.
"""

import asyncio
import json

from integrations.monzo import MonzoClient, MonzoError


async def main() -> None:
    client = MonzoClient()
    if not client.configured:
        raise SystemExit(
            "Monzo not configured. Set MONZO_ACCESS_TOKEN and MONZO_ACCOUNT_ID in .env first."
        )

    try:
        bal = await client.fetch_balance()
        print("=== BALANCE ===")
        print(json.dumps(bal, indent=2))
        total = await client.total_gbp()
        print(f"\n=== TOTAL (GBP) ===\n  £{total:.2f}")
    except MonzoError as e:
        raise SystemExit(f"Monzo error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
