"""Throwaway smoke test: prove the Coinbase connection works, print balances.

Run AFTER putting your CDP key in api/.env (COINBASE_API_KEY_NAME +
COINBASE_API_PRIVATE_KEY):

    .venv/bin/python -m scripts.coinbase_smoke

Does NOT touch the database. Delete once you trust the integration.
"""

import asyncio
from decimal import Decimal

from integrations.coinbase import CoinbaseClient, CoinbaseError


async def main() -> None:
    client = CoinbaseClient()
    if not client.configured:
        raise SystemExit(
            "No Coinbase key found. Set COINBASE_API_KEY_NAME and "
            "COINBASE_API_PRIVATE_KEY in api/.env first."
        )

    try:
        accounts = await client.fetch_accounts()
        print(f"=== ACCOUNTS ({len(accounts)}) ===")
        for acct in accounts:
            bal = acct.get("balance") or {}
            amount = Decimal(str(bal.get("amount", "0")))
            if amount != 0:
                print(f"  {bal.get('currency'):>6}  {amount}")

        total = await client.total_gbp()
        print(f"\n=== TOTAL (GBP) ===\n  £{total:.2f}")
    except CoinbaseError as e:
        raise SystemExit(f"Coinbase error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
