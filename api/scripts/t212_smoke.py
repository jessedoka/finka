"""Throwaway smoke test: prove the T212 connection works, print raw JSON.

Run AFTER you've put your real key in api/.env as `trading_212_key=...`:

    .venv/bin/python -m scripts.t212_smoke

This does NOT touch the database. It's here so you can see your real numbers
come back before you write the mapping service. Delete it once the real sync
exists.
"""

import asyncio
import json

from integrations.trading212 import Trading212Client, Trading212Error


async def main() -> None:
    client = Trading212Client()
    if client.api_key in ("", "local", None):
        raise SystemExit("No real key found. Set trading_212_key in api/.env first.")

    try:
        cash = await client.fetch_cash()
        print("=== CASH ===")
        print(json.dumps(cash, indent=2))

        portfolio = await client.fetch_portfolio()
        print(f"\n=== PORTFOLIO ({len(portfolio)} positions) ===")
        print(json.dumps(portfolio, indent=2))
    except Trading212Error as e:
        raise SystemExit(f"T212 error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
