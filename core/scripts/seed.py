"""Seed the local dev user plus a couple of sample manual accounts.

Enough to render the dashboard on a fresh database. Real data sources are added
through the Connections page at runtime (or via scripts/seed_connections.py),
not here.
"""

import asyncio
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from config import settings
from models.account import Account
from models.user import User

engine = create_async_engine(settings.database_url)
async_session = async_sessionmaker(engine, expire_on_commit=False)

DEV_USER_SUB = "dev-user-001"

SAMPLE_ACCOUNTS = [
    # A liquid account and a locked one, so the spendable/long-term split has
    # something to show.
    {
        "name": "Savings",
        "account_type": "savings",
        "institution": "Example Bank",
        "balance": Decimal("5200.00"),
        "is_long_term": False,
    },
    {
        "name": "Pension",
        "account_type": "pension",
        "institution": "Example Pension Co",
        "balance": Decimal("12400.00"),
        "is_long_term": True,
        "monthly_contribution": Decimal("250.00"),
        "growth_rate": Decimal("0.05"),
    },
]


async def seed() -> None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.cognito_sub == DEV_USER_SUB))
        if user is None:
            user = User(cognito_sub=DEV_USER_SUB, email="dev@finka.local", display_name="Dev")
            session.add(user)
            await session.flush()
            print(f"Created dev user {DEV_USER_SUB}")
        else:
            print(f"Dev user {DEV_USER_SUB} already exists")

        existing = set(
            (await session.scalars(select(Account.name).where(Account.user_id == user.id))).all()
        )
        added = 0
        for data in SAMPLE_ACCOUNTS:
            if data["name"] in existing:
                continue
            session.add(Account(user_id=user.id, currency="GBP", **data))
            added += 1

        await session.commit()
        print(f"Seeded {added} sample account(s). Add real sources on the Connections page.")


if __name__ == "__main__":
    asyncio.run(seed())
