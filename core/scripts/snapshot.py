"""Record today's net-worth snapshot (manual trigger — Phase 0).

Run it whenever you want to add a point to the history chart:

    .venv/bin/python -m scripts.snapshot

Re-running on the same day overwrites that day's row (idempotent). Later this
same call becomes an AWS EventBridge schedule -> Lambda, so the "how do I run
this daily?" question is itself Milestone 3/6 material.

Needs local Postgres up, migrations applied, and the dev user seeded.
"""

import asyncio

from database import async_session
from query_selectors.user_selector import UserSelector
from services.net_worth_service import NetWorthService

DEV_USER_SUB = "dev-user-001"


async def main() -> None:
    async with async_session() as db:
        user = await db.scalar(UserSelector(DEV_USER_SUB).records)
        if user is None:
            raise SystemExit(
                f"No user with cognito_sub={DEV_USER_SUB!r}. Run scripts/seed.py first."
            )

        snapshot = await NetWorthService(db).record_snapshot(user.id)
        print(
            f"Recorded snapshot for {snapshot.snapshot_date}: "
            f"total_assets={snapshot.total_assets}"
        )


if __name__ == "__main__":
    asyncio.run(main())
