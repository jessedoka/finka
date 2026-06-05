from datetime import date
from uuid import UUID

from sqlalchemy.dialects import postgresql

from query_selectors.transaction_selector import TransactionSelector

USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def compile_stmt(stmt):
    compiled = stmt.compile(dialect=postgresql.dialect())
    return str(compiled), compiled.params


def test_base_query_filters_by_user():
    sel = TransactionSelector(USER_ID)
    sql, params = compile_stmt(sel.records)
    assert "transactions.user_id" in sql
    assert USER_ID in params.values()


def test_base_query_orders_by_date_desc():
    sel = TransactionSelector(USER_ID)
    sql, _ = compile_stmt(sel.records)
    assert "ORDER BY" in sql.upper()
    assert "transaction_date" in sql
    assert "DESC" in sql.upper()


def test_select_within_a_year_adds_date_range():
    sel = TransactionSelector(USER_ID).select_within_a_year(3, 2024)
    sql, params = compile_stmt(sel.records)
    assert "transaction_date" in sql
    assert date(2024, 3, 1) in params.values()
    assert date(2024, 4, 1) in params.values()


def test_select_within_a_year_december_wraps_to_next_year():
    sel = TransactionSelector(USER_ID).select_within_a_year(12, 2024)
    _, params = compile_stmt(sel.records)
    assert date(2024, 12, 1) in params.values()
    assert date(2025, 1, 1) in params.values()


def test_select_by_account_adds_account_filter():
    sel = TransactionSelector(USER_ID).select_by_account(42)
    sql, params = compile_stmt(sel.records)
    assert "account_id" in sql
    assert 42 in params.values()


def test_select_by_transaction_adds_id_filter():
    sel = TransactionSelector(USER_ID).select_by_transaction(99)
    sql, params = compile_stmt(sel.records)
    assert "transactions.id" in sql
    assert 99 in params.values()


def test_chaining_preserves_all_filters():
    sel = (
        TransactionSelector(USER_ID)
        .select_within_a_year(6, 2023)
        .select_by_account(5)
        .select_by_transaction(10)
    )
    sql, params = compile_stmt(sel.records)
    values = list(params.values())
    assert USER_ID in values
    assert date(2023, 6, 1) in values
    assert date(2023, 7, 1) in values
    assert 5 in values
    assert 10 in values


def test_chaining_returns_selector_for_fluent_interface():
    sel = TransactionSelector(USER_ID)
    assert sel.select_by_account(1) is sel
    assert sel.select_within_a_year(1, 2024) is sel
    assert sel.select_by_transaction(1) is sel
