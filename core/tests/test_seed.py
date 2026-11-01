"""`scripts.seed` runs on every `./start.sh`, so it must leave real data alone.

The regression: deleted samples came back on the next start and were counted in
that day's snapshot, adding £17,600 of made-up money to the net-worth history.
"""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select

from models.account import Account
from models.net_worth_snapshot import NetWorthSnapshot
from scripts import seed as seed_script


@pytest.fixture(autouse=True)
def use_test_db(monkeypatch, sessionmaker):
    monkeypatch.setattr(seed_script, "async_session", sessionmaker)
    monkeypatch.setattr(seed_script, "DEV_USER_SUB", "test-user-001")


async def _account_names(session):
    return set((await session.scalars(select(Account.name))).all())


async def test_empty_setup_gets_the_samples_once(session):
    await seed_script.seed()
    await seed_script.seed()

    assert sorted((await session.scalars(select(Account.name))).all()) == ["Pension", "Savings"]


async def test_samples_stay_out_when_real_accounts_exist(session, user):
    session.add(
        Account(
            user_id=user.id,
            name="Tembo LISA",
            account_type="savings",
            balance=Decimal("5409.90"),
        )
    )
    await session.commit()

    await seed_script.seed()

    assert await _account_names(session) == {"Tembo LISA"}


async def test_deleted_samples_stay_deleted_once_history_exists(session, user):
    session.add(
        NetWorthSnapshot(
            user_id=user.id,
            snapshot_date=date(2026, 10, 23),
            total_assets=Decimal("19696.13"),
            total_liabilities=Decimal("0"),
            net_worth=Decimal("19696.13"),
        )
    )
    await session.commit()

    await seed_script.seed()

    assert await _account_names(session) == set()
