"""Seed a fully populated demo: fictional accounts, 18 months of history, goals.

For showing Finka off without anyone's real finances. All names and numbers are
made up. Refuses to run on a database that already holds data, so it can never
overwrite a real setup; `./start.sh --demo` runs it in its own throwaway
Docker project for that reason.
"""

import asyncio
import random
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config import settings
from models.account import Account
from models.connection import Connection
from models.goal import Goal, GoalAllocation
from models.net_worth_snapshot import NetWorthSnapshot
from models.user import User

engine = create_async_engine(settings.database_url)
async_session = async_sessionmaker(engine, expire_on_commit=False)

DEV_USER_SUB = "dev-user-001"
HISTORY_WEEKS = 78
SEED = 42  # fixed, so the demo looks the same every time

# name, type, institution, balance today, long-term?, monthly saved, annual growth
ACCOUNTS = [
    ("Current Account", "current", "Demo Bank", 1850, False, 0, 0.0),
    ("Travel Fund", "savings", "Demo Bank", 4200, False, 450, 0.0),
    ("Emergency Fund", "savings", "Demo Bank", 6000, False, 150, 0.0),
    ("Index Funds", "investment", "Demo Broker", 9300, False, 300, 0.07),
    ("Workplace Pension", "pension", "Demo Pension Co", 14800, True, 280, 0.05),
    ("Lifetime ISA", "isa", "Demo Bank", 5100, True, 200, 0.04),
]


def history(final: float, monthly: float, growth: float, weeks_ago: int, rng: random.Random) -> float:
    """Walk a balance backwards from today: undo contributions and growth, add noise."""
    months = weeks_ago / 4.345
    value = (final - monthly * months) / ((1 + growth) ** (months / 12))
    noise = rng.uniform(-0.01, 0.01) * final if monthly or growth else rng.uniform(-300, 300)
    return max(value + noise, 0.0)


async def seed_demo() -> None:
    rng = random.Random(SEED)
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.cognito_sub == DEV_USER_SUB))
        if user is None:
            user = User(cognito_sub=DEV_USER_SUB, email="demo@finka.local", display_name="Demo")
            session.add(user)
            await session.flush()

        # Safety: never touch a database that already holds anything.
        for model in (Account, Connection, Goal, NetWorthSnapshot):
            count = await session.scalar(
                select(func.count()).select_from(model).where(model.user_id == user.id)
            )
            if count:
                raise SystemExit(
                    f"Refusing to seed demo data: {model.__tablename__} already has rows. "
                    "Use an empty database (`./start.sh --demo` uses its own)."
                )

        for name, kind, inst, balance, long_term, monthly, growth in ACCOUNTS:
            session.add(
                Account(
                    user_id=user.id,
                    name=name,
                    account_type=kind,
                    institution=inst,
                    currency="GBP",
                    balance=Decimal(balance),
                    is_long_term=long_term,
                    monthly_contribution=Decimal(monthly),
                    growth_rate=Decimal(str(growth)),
                )
            )

        today = date.today()
        for weeks_ago in range(HISTORY_WEEKS, -1, -1):
            breakdown = {}
            for name, _, _, balance, _, monthly, growth in ACCOUNTS:
                value = balance if weeks_ago == 0 else history(balance, monthly, growth, weeks_ago, rng)
                breakdown[f"account:{name}"] = round(value, 2)
            total = Decimal(str(round(sum(breakdown.values()), 2)))
            session.add(
                NetWorthSnapshot(
                    user_id=user.id,
                    snapshot_date=today - timedelta(weeks=weeks_ago),
                    total_assets=total,
                    total_liabilities=Decimal("0.00"),
                    net_worth=total,
                    breakdown=breakdown,
                )
            )

        travel = Goal(
            user_id=user.id,
            name="Travel fund",
            target_amount=Decimal("6000"),
            target_date=today + timedelta(days=150),
            ring_fenced=True,
            notes="Demo goal: money set aside for a big trip.",
        )
        emergency = Goal(
            user_id=user.id,
            name="Emergency fund",
            target_amount=Decimal("9000"),
            notes="Demo goal: three months of costs.",
        )
        session.add_all([travel, emergency])
        await session.flush()
        session.add_all(
            [
                GoalAllocation(goal_id=travel.id, source_key="account:Travel Fund"),
                GoalAllocation(goal_id=emergency.id, source_key="account:Emergency Fund"),
            ]
        )

        await session.commit()
        print(
            f"Seeded demo: {len(ACCOUNTS)} accounts, {HISTORY_WEEKS + 1} weekly snapshots, 2 goals."
        )


if __name__ == "__main__":
    asyncio.run(seed_demo())
