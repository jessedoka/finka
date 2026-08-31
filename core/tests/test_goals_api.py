"""End-to-end goals flow through the real FastAPI app + ORM (in-memory SQLite).

Covers the whole story from the design discussion: create a goal, earmark a real
source, cap a partial slice at the live balance, and — the point of ring-fencing —
carve committed money out of Spendable in the net-worth split.
"""

from decimal import Decimal

import pytest

from models.account import Account

GOALS = "/api/goals/"
BREAKDOWN = "/api/net-worth/breakdown"


async def _seed_account(session, user, name, balance, *, is_long_term=False):
    session.add(
        Account(
            user_id=user.id,
            name=name,
            account_type="savings",
            balance=Decimal(str(balance)),
            is_active=True,
            is_long_term=is_long_term,
        )
    )
    await session.commit()


async def _create_goal(client, **body):
    body.setdefault("name", "Trip")
    body.setdefault("target_amount", 22000)
    res = await client.post(GOALS, json=body)
    assert res.status_code == 201, res.text
    return res.json()


@pytest.mark.asyncio
async def test_create_and_list_goal(client):
    goal = await _create_goal(client, name="Asia 2027", target_amount=22000)
    assert goal["name"] == "Asia 2027"
    assert goal["target"] == 22000.0
    assert goal["funded"] == 0.0
    assert goal["remaining"] == 22000.0
    assert goal["reached"] is False
    assert goal["allocations"] == []

    listed = (await client.get(GOALS)).json()
    assert [g["id"] for g in listed] == [goal["id"]]


@pytest.mark.asyncio
async def test_earmark_whole_account_funds_goal(client, session, user):
    await _seed_account(session, user, "Savings", 8000)
    goal = await _create_goal(client, target_amount=22000)

    res = await client.post(f"{GOALS}{goal['id']}/allocations", json={"source_key": "account:Savings"})
    assert res.status_code == 201, res.text
    detail = res.json()

    assert detail["funded"] == 8000.0
    assert detail["remaining"] == 14000.0
    assert len(detail["allocations"]) == 1
    assert detail["allocations"][0]["counted"] == 8000.0
    assert detail["allocations"][0]["id"] is not None  # needed by the UI to remove it


@pytest.mark.asyncio
async def test_partial_slice_capped_at_balance(client, session, user):
    # £5,200 earmarked from a pot that only holds £4,000 -> funded counts £4,000.
    await _seed_account(session, user, "Savings", 4000)
    goal = await _create_goal(client, target_amount=10000)

    res = await client.post(
        f"{GOALS}{goal['id']}/allocations",
        json={"source_key": "account:Savings", "allocated_amount": 5200},
    )
    detail = res.json()
    assert detail["allocations"][0]["counted"] == 4000.0
    assert detail["funded"] == 4000.0


@pytest.mark.asyncio
async def test_ring_fenced_goal_carves_committed_out_of_spendable(client, session, user):
    # £10k liquid across two accounts; ring-fence a £5,200 slice of Savings.
    await _seed_account(session, user, "Savings", 8000)
    await _seed_account(session, user, "Current", 2000)
    goal = await _create_goal(client, name="WHV proof of funds", target_amount=5200, ring_fenced=True)
    await client.post(
        f"{GOALS}{goal['id']}/allocations",
        json={"source_key": "account:Savings", "allocated_amount": 5200},
    )

    split = (await client.get(BREAKDOWN)).json()
    assert split["net_worth"] == 10000.0
    assert split["committed"] == 5200.0
    assert split["committed_keys"] == ["account:Savings"]
    # Only the slice leaves spendable; the other £2,800 of Savings stays.
    assert split["spendable"] == 4800.0
    assert split["committed_by_key"]["account:Savings"] == 5200.0


@pytest.mark.asyncio
async def test_non_ring_fenced_goal_does_not_carve(client, session, user):
    await _seed_account(session, user, "Savings", 8000)
    goal = await _create_goal(client, target_amount=5000, ring_fenced=False)
    await client.post(f"{GOALS}{goal['id']}/allocations", json={"source_key": "account:Savings"})

    split = (await client.get(BREAKDOWN)).json()
    assert split["committed"] == 0.0
    assert split["spendable"] == 8000.0  # nothing carved out


@pytest.mark.asyncio
async def test_duplicate_earmark_conflicts(client, session, user):
    await _seed_account(session, user, "Savings", 8000)
    goal = await _create_goal(client)
    first = await client.post(f"{GOALS}{goal['id']}/allocations", json={"source_key": "account:Savings"})
    assert first.status_code == 201
    dup = await client.post(f"{GOALS}{goal['id']}/allocations", json={"source_key": "account:Savings"})
    assert dup.status_code == 409


@pytest.mark.asyncio
async def test_bad_source_key_rejected(client):
    goal = await _create_goal(client)
    res = await client.post(f"{GOALS}{goal['id']}/allocations", json={"source_key": "savings"})
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_remove_allocation_and_delete_goal(client, session, user):
    await _seed_account(session, user, "Savings", 8000)
    goal = await _create_goal(client)
    detail = (
        await client.post(f"{GOALS}{goal['id']}/allocations", json={"source_key": "account:Savings"})
    ).json()
    alloc_id = detail["allocations"][0]["id"]

    after_remove = (await client.delete(f"{GOALS}{goal['id']}/allocations/{alloc_id}")).json()
    assert after_remove["allocations"] == []
    assert after_remove["funded"] == 0.0

    assert (await client.delete(f"{GOALS}{goal['id']}")).status_code == 204
    assert (await client.get(f"{GOALS}{goal['id']}")).status_code == 404
