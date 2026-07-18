import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

from fastapi import HTTPException

from services.transaction_service import TransactionService
from schemas.transaction import TransactionCreate
from models.transaction import Transaction

USER_ID = UUID("00000000-0000-0000-0000-000000000001")
OTHER_USER_ID = UUID("00000000-0000-0000-0000-000000000002")


def make_tx(**overrides) -> Transaction:
    tx = Transaction(
        id=1,
        user_id=USER_ID,
        account_id=1,
        amount=Decimal("10.00"),
        description="Test transaction",
        merchant_name=None,
        transaction_date=date(2024, 3, 15),
        category_id=None,
    )
    for k, v in overrides.items():
        setattr(tx, k, v)
    return tx


@pytest.fixture
def db():
    session = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def service(db):
    return TransactionService(db)


# --- list_transaction ---

async def test_list_transaction_no_filters(service, db):
    tx = make_tx()
    result = MagicMock()
    result.scalars.return_value.all.return_value = [tx]
    db.execute.return_value = result

    items = await service.list_transaction(USER_ID, None, None, None)

    assert items == [tx]
    db.execute.assert_awaited_once()


async def test_list_transaction_with_month_year(service, db):
    tx = make_tx()
    result = MagicMock()
    result.scalars.return_value.all.return_value = [tx]
    db.execute.return_value = result

    items = await service.list_transaction(USER_ID, 3, 2024, None)

    assert items == [tx]


async def test_list_transaction_with_account_id(service, db):
    tx = make_tx()
    result = MagicMock()
    result.scalars.return_value.all.return_value = [tx]
    db.execute.return_value = result

    items = await service.list_transaction(USER_ID, None, None, account_id=1)

    assert items == [tx]


async def test_list_transaction_empty_result(service, db):
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    db.execute.return_value = result

    items = await service.list_transaction(USER_ID, None, None, None)

    assert items == []


# --- create ---

async def test_create_adds_and_commits(service, db):
    data = TransactionCreate(
        account_id=1,
        amount=Decimal("25.50"),
        description="Coffee",
        transaction_date=date(2024, 3, 1),
    )

    await service.create(USER_ID, data)

    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()


async def test_create_sets_user_id(service, db):
    data = TransactionCreate(
        account_id=2,
        amount=Decimal("5.00"),
        description="Bus",
        transaction_date=date(2024, 4, 10),
    )

    await service.create(USER_ID, data)

    added_tx = db.add.call_args[0][0]
    assert added_tx.user_id == USER_ID


async def test_create_returns_refreshed_transaction(service, db):
    data = TransactionCreate(
        account_id=1,
        amount=Decimal("100.00"),
        description="Salary",
        transaction_date=date(2024, 4, 1),
    )
    tx = make_tx()

    async def fake_refresh(obj):
        obj.id = tx.id

    db.refresh.side_effect = fake_refresh

    result = await service.create(USER_ID, data)
    assert result.id == tx.id


# --- update_category ---

async def test_update_category_success(service, db):
    tx = make_tx(category_id=None)
    db.scalar.return_value = tx

    result = await service.update_category(1, USER_ID, 5)

    assert result.category_id == 5
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()


async def test_update_category_clears_category(service, db):
    tx = make_tx(category_id=5)
    db.scalar.return_value = tx

    result = await service.update_category(1, USER_ID, None)

    assert result.category_id is None


async def test_update_category_not_found_raises_404(service, db):
    db.scalar.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await service.update_category(999, USER_ID, 5)

    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail.lower()


# --- delete ---

async def test_delete_success(service, db):
    tx = make_tx()
    db.scalar.return_value = tx

    await service.delete(1, USER_ID)

    db.delete.assert_awaited_once_with(tx)
    db.commit.assert_awaited_once()


async def test_delete_not_found_raises_404(service, db):
    db.scalar.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await service.delete(999, USER_ID)

    assert exc_info.value.status_code == 404


async def test_delete_does_not_delete_other_users_transaction(service, db):
    db.scalar.return_value = None  # selector filters by user_id, returns None

    with pytest.raises(HTTPException) as exc_info:
        await service.delete(1, OTHER_USER_ID)

    assert exc_info.value.status_code == 404
    db.delete.assert_not_awaited()
