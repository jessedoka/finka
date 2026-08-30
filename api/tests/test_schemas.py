"""Pydantic schema defaults and validation for accounts, connections, and goals."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from schemas.account import AccountBase, AccountCreate, AccountUpdate, AccountResponse
from schemas.connection import (
    ConnectionBase,
    ConnectionCreate,
    ConnectionUpdate,
    ConnectionResponse,
    ConnectionTestRequest,
    ConnectionTestResult,
)
from schemas.goal import GoalCreate, GoalUpdate, AllocationCreate


def test_account_base_defaults():
    account = AccountBase(name="Savings", account_type="savings")
    assert account.currency == "GBP"
    assert account.institution is None
    assert account.balance == Decimal("0.00")
    assert account.is_active is True
    assert account.is_long_term is False
    assert account.monthly_contribution == Decimal("0.00")
    assert account.annual_charge == Decimal("0.00")
    assert account.growth_rate == Decimal("0.05")


def test_account_base_requires_name_and_type():
    with pytest.raises(ValidationError):
        AccountBase(account_type="savings")


def test_account_create_accepts_overrides():
    account = AccountCreate(
        name="Pension",
        account_type="pension",
        currency="USD",
        balance=Decimal("1500.50"),
        is_long_term=True,
    )
    assert account.currency == "USD"
    assert account.balance == Decimal("1500.50")
    assert account.is_long_term is True


def test_account_update_all_fields_default_none():
    update = AccountUpdate()
    assert update.name is None
    assert update.account_type is None
    assert update.currency is None
    assert update.balance is None
    assert update.is_active is None
    assert update.growth_rate is None


def test_account_update_partial_fields():
    update = AccountUpdate(balance=Decimal("200.00"))
    assert update.balance == Decimal("200.00")
    assert update.name is None


def test_account_response_requires_id():
    with pytest.raises(ValidationError):
        AccountResponse(name="Savings", account_type="savings")


def test_account_response_with_id():
    response = AccountResponse(id=1, name="Savings", account_type="savings")
    assert response.id == 1
    assert response.currency == "GBP"


def test_connection_base_defaults():
    connection = ConnectionBase(provider="monzo", label="My Monzo")
    assert connection.config == {}
    assert connection.is_active is True
    assert connection.is_long_term is False


def test_connection_create_requires_provider_and_label():
    with pytest.raises(ValidationError):
        ConnectionCreate(label="My Monzo")


def test_connection_update_all_optional():
    update = ConnectionUpdate()
    assert update.label is None
    assert update.config is None
    assert update.is_active is None
    assert update.is_long_term is None


def test_connection_response_requires_all_named_fields():
    response = ConnectionResponse(
        id=1,
        provider="monzo",
        label="My Monzo",
        is_active=True,
        is_long_term=False,
        config={},
    )
    assert response.last_synced_at is None
    assert response.last_status is None
    assert response.last_error is None
    assert response.last_value is None


def test_connection_test_request_defaults():
    request = ConnectionTestRequest(provider="trading212")
    assert request.config == {}


def test_connection_test_result_defaults():
    result = ConnectionTestResult(ok=True)
    assert result.value is None
    assert result.error is None


def test_goal_create_defaults():
    goal = GoalCreate(name="Trip", target_amount=Decimal("1000"))
    assert goal.currency == "GBP"
    assert goal.ring_fenced is False
    assert goal.notes is None
    assert goal.target_date is None


def test_goal_create_target_amount_must_be_positive():
    with pytest.raises(ValidationError):
        GoalCreate(name="Trip", target_amount=Decimal("0"))


def test_goal_create_target_amount_rejects_negative():
    with pytest.raises(ValidationError):
        GoalCreate(name="Trip", target_amount=Decimal("-100"))


def test_goal_update_all_optional():
    update = GoalUpdate()
    assert update.name is None
    assert update.target_amount is None
    assert update.target_date is None
    assert update.notes is None


def test_goal_update_target_amount_must_be_positive_when_set():
    with pytest.raises(ValidationError):
        GoalUpdate(target_amount=Decimal("0"))


def test_allocation_create_defaults_to_whole_source():
    allocation = AllocationCreate(source_key="account:Savings")
    assert allocation.allocated_amount is None


def test_allocation_create_rejects_non_positive_amount():
    with pytest.raises(ValidationError):
        AllocationCreate(source_key="account:Savings", allocated_amount=Decimal("0"))
