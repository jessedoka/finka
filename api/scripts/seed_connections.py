"""Seed Connection rows from the legacy env vars (backward compat).

Before connections existed, providers were configured via a single global
.env (see config.py). This script migrates those values into per-user
Connection rows for the dev user so the existing setup keeps working after the
schema change. Idempotent: skips a provider if the user already has a
connection for it.

Run once after `alembic upgrade head`:  uv run python -m scripts.seed_connections
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from config import settings
from models.connection import Connection
from models.user import User

engine = create_async_engine(settings.database_url)
async_session = async_sessionmaker(engine, expire_on_commit=False)


def _seeds() -> list[dict]:
    """One dict per configured legacy provider — empty creds are skipped."""
    out: list[dict] = []

    if settings.trading_212_key and settings.trading_212_key != "local":
        out.append({
            "provider": "trading212",
            "label": "Trading212",
            "config": {"api_key": settings.trading_212_key},
        })

    if settings.coinbase_api_key_name and settings.coinbase_api_private_key:
        out.append({
            "provider": "coinbase",
            "label": "Coinbase",
            "config": {
                "api_key_name": settings.coinbase_api_key_name,
                "api_private_key": settings.coinbase_api_private_key,
            },
        })

    if settings.monzo_access_token and settings.monzo_account_id:
        config = {
            "access_token": settings.monzo_access_token,
            "account_id": settings.monzo_account_id,
        }
        # Fold the old projection knobs into the connection's config.
        if settings.monzo_pots_monthly_contribution:
            config["monthly_contribution"] = settings.monzo_pots_monthly_contribution
        if settings.monzo_pots_growth_rate:
            config["growth_rate"] = settings.monzo_pots_growth_rate
        out.append({"provider": "monzo", "label": "Monzo pots", "config": config})

    return out


async def seed_connections():
    async with async_session() as session:
        user = await session.scalar(
            select(User).where(User.cognito_sub == "dev-user-001")
        )
        if user is None:
            print("No dev user (cognito_sub=dev-user-001); run scripts.seed first.")
            return

        existing = set(
            await session.scalars(
                select(Connection.provider).where(Connection.user_id == user.id)
            )
        )

        created = 0
        for seed in _seeds():
            if seed["provider"] in existing:
                print(f"skip {seed['provider']}: already has a connection")
                continue
            session.add(Connection(user_id=user.id, **seed))
            created += 1
            print(f"seeded {seed['provider']} -> {seed['label']!r}")

        await session.commit()
        print(f"Done: {created} connection(s) created.")


if __name__ == "__main__":
    asyncio.run(seed_connections())
