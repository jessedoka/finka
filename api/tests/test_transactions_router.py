import pytest
from decimal import Decimal
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID

import httpx
from fastapi import HTTPException
from httpx import ASGITransport

from main import app
from database import get_db
from routers.transactions import get_service

USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def make_tx(**overrides):
    """Return a namespace that Pydantic can serialize via from_attributes."""
    defaults = dict(
        id=1,
        user_id=USER_ID,
        account_id=1,
        amount=Decimal("10.00"),
        description="Test",
        merchant_name=None,
        transaction_date=date(2024, 3, 15),
        category_id=None,
        category_name=None,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


@pytest.fixture
def mock_service():
    return AsyncMock()


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.scalar.return_value = 0
    return db


@pytest.fixture
async def client(mock_service, mock_db):
    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_service] = lambda: mock_service
    app.dependency_overrides[get_db] = override_get_db

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c

    app.dependency_overrides.clear()


# --- GET /api/transactions/ ---

async def test_list_transactions_returns_200(client, mock_service):
    mock_service.list_transaction.return_value = [make_tx()]

    resp = await client.get("/api/transactions/", params={"month": 3, "year": 2024, "account_id": 1})

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == 1
    assert data[0]["description"] == "Test"


async def test_list_transactions_passes_filters_to_service(client, mock_service):
    mock_service.list_transaction.return_value = []

    await client.get("/api/transactions/", params={"month": 6, "year": 2023, "account_id": 2})

    mock_service.list_transaction.assert_awaited_once_with(USER_ID, 6, 2023, 2)


async def test_list_transactions_empty(client, mock_service):
    mock_service.list_transaction.return_value = []

    resp = await client.get("/api/transactions/", params={"month": 1, "year": 2024, "account_id": 1})

    assert resp.status_code == 200
    assert resp.json() == []


# --- GET /api/transactions/count ---

async def test_transaction_count(client, mock_db):
    mock_db.scalar.return_value = 42

    resp = await client.get("/api/transactions/count")

    assert resp.status_code == 200
    assert resp.json() == {"count": 42}


# --- POST /api/transactions/ ---

async def test_create_transaction_returns_201(client, mock_service):
    mock_service.create.return_value = make_tx(id=5, description="Coffee", amount=Decimal("3.50"))

    resp = await client.post("/api/transactions/", json={
        "account_id": 1,
        "amount": "3.50",
        "description": "Coffee",
        "transaction_date": "2024-03-15",
    })

    assert resp.status_code == 201
    assert resp.json()["id"] == 5
    assert resp.json()["description"] == "Coffee"


async def test_create_transaction_passes_user_id_to_service(client, mock_service):
    mock_service.create.return_value = make_tx()

    await client.post("/api/transactions/", json={
        "account_id": 1,
        "amount": "10.00",
        "description": "Test",
        "transaction_date": "2024-03-15",
    })

    call_user_id = mock_service.create.call_args[0][0]
    assert call_user_id == USER_ID


async def test_create_transaction_invalid_body_returns_422(client, mock_service):
    resp = await client.post("/api/transactions/", json={"description": "Missing required fields"})

    assert resp.status_code == 422
    mock_service.create.assert_not_awaited()


# --- PATCH /api/transactions/{tx_id}/category ---

async def test_update_category_returns_200(client, mock_service):
    mock_service.update_category.return_value = make_tx(category_id=3)

    resp = await client.patch("/api/transactions/1/category", json={"category_id": 3})

    assert resp.status_code == 200
    assert resp.json()["category_id"] == 3


async def test_update_category_passes_correct_args(client, mock_service):
    mock_service.update_category.return_value = make_tx(category_id=7)

    await client.patch("/api/transactions/10/category", json={"category_id": 7})

    mock_service.update_category.assert_awaited_once_with(10, USER_ID, 7)


async def test_update_category_not_found_returns_404(client, mock_service):
    mock_service.update_category.side_effect = HTTPException(
        status_code=404, detail="Transaction not found"
    )

    resp = await client.patch("/api/transactions/999/category", json={"category_id": 1})

    assert resp.status_code == 404


async def test_update_category_clear_category(client, mock_service):
    mock_service.update_category.return_value = make_tx(category_id=None)

    resp = await client.patch("/api/transactions/1/category", json={"category_id": None})

    assert resp.status_code == 200
    assert resp.json()["category_id"] is None


# --- DELETE /api/transactions/{tx_id} ---

async def test_delete_transaction_returns_204(client, mock_service):
    mock_service.delete.return_value = None

    resp = await client.delete("/api/transactions/1")

    assert resp.status_code == 204
    mock_service.delete.assert_awaited_once_with(1, USER_ID)


async def test_delete_transaction_not_found_returns_404(client, mock_service):
    mock_service.delete.side_effect = HTTPException(
        status_code=404, detail="Transaction not found"
    )

    resp = await client.delete("/api/transactions/999")

    assert resp.status_code == 404
