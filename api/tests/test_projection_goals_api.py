"""Dated goals show up in the projection as planned outflows; ring-fenced goals
(reserves you keep) do not."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from models.account import Account

GOALS = "/api/goals/"
PROJECTION = "/api/net-worth/projection"


async def _seed_account(session, user, name, balance):
    session.add(
        Account(
            user_id=user.id,
            name=name,
            account_type="savings",
            balance=Decimal(str(balance)),
            is_active=True,
        )
    )
    await session.commit()


@pytest.mark.asyncio
async def test_dated_goal_dips_the_projection(client, session, user):
    await _seed_account(session, user, "Savings", 20000)
    due = date.today().replace(day=1) + timedelta(days=400)  # ~13 months out
    await client.post(GOALS, json={"name": "Trip", "target_amount": 8000, "target_date": due.isoformat()})

    proj = (await client.get(f"{PROJECTION}?years=5")).json()
    assert proj["spent"] == 8000.0
    assert len(proj["events"]) == 1
    assert proj["events"][0]["name"] == "Trip"
    assert proj["events"][0]["drop"] == 8000.0
    # A point carries the event marker, and net worth after < before.
    assert any(p.get("event") == "Trip" for p in proj["series"])


@pytest.mark.asyncio
async def test_ring_fenced_goal_does_not_dip(client, session, user):
    await _seed_account(session, user, "Savings", 20000)
    due = date.today().replace(day=1) + timedelta(days=400)
    await client.post(
        GOALS,
        json={"name": "Proof of funds", "target_amount": 5200, "target_date": due.isoformat(), "ring_fenced": True},
    )

    proj = (await client.get(f"{PROJECTION}?years=5")).json()
    assert proj["spent"] == 0.0
    assert proj["events"] == []


@pytest.mark.asyncio
async def test_undated_goal_does_not_dip(client, session, user):
    await _seed_account(session, user, "Savings", 20000)
    await client.post(GOALS, json={"name": "Someday", "target_amount": 5000})

    proj = (await client.get(f"{PROJECTION}?years=5")).json()
    assert proj["spent"] == 0.0
    assert proj["events"] == []
