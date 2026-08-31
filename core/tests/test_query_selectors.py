import uuid

from query_selectors.account_selector import AccountSelector
from query_selectors.user_selector import UserSelector


def test_account_selector_stores_user_id():
    user_id = uuid.uuid4()
    selector = AccountSelector(user_id)
    assert selector.user_id == user_id


def test_account_selector_records_filters_by_user_and_orders_newest_first():
    user_id = uuid.uuid4()
    selector = AccountSelector(user_id)
    compiled = str(selector.records.compile())
    assert "WHERE accounts.user_id" in compiled
    assert "ORDER BY accounts.created_at DESC" in compiled


def test_account_selector_by_account_filters_by_id_and_user():
    user_id = uuid.uuid4()
    selector = AccountSelector(user_id)
    compiled = str(selector.select_by_account(42).compile())
    assert "WHERE accounts.id" in compiled
    assert "AND accounts.user_id" in compiled


def test_user_selector_filters_by_cognito_sub():
    selector = UserSelector("cognito-sub-123")
    compiled = str(selector.records.compile())
    assert "WHERE users.cognito_sub" in compiled


def test_user_selector_limits_to_one_row():
    selector = UserSelector("cognito-sub-123")
    compiled = str(selector.records.compile())
    assert "LIMIT" in compiled
