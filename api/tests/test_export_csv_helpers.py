"""CSV export helpers: row serialisation, JSON-field cells, and breakdown
pivoting for net-worth snapshots."""

import csv
import io

from services.export_service import ACCOUNT_CSV_FIELDS, _rows_to_csv, _snapshots_to_csv


def test_rows_to_csv_writes_header_and_values():
    rows = [{"id": 1, "name": "Savings", "account_type": "savings", "currency": "GBP",
             "institution": None, "balance": "5200.00", "is_active": True,
             "is_long_term": False, "monthly_contribution": "0.00",
             "annual_charge": "0.00", "growth_rate": "0.0500",
             "created_at": "2026-01-01T00:00:00+00:00", "updated_at": "2026-01-01T00:00:00+00:00"}]

    text = _rows_to_csv(rows, ACCOUNT_CSV_FIELDS)
    parsed = list(csv.DictReader(io.StringIO(text)))

    assert parsed[0]["name"] == "Savings"
    assert parsed[0]["balance"] == "5200.00"
    assert parsed[0]["institution"] == ""


def test_rows_to_csv_dumps_json_fields_as_string():
    rows = [{"id": 1, "provider": "monzo", "label": "Monzo",
             "config": {"account_id": "acc_123"}, "is_active": True}]

    text = _rows_to_csv(rows, ["id", "provider", "label", "config", "is_active"],
                         json_fields={"config"})
    parsed = list(csv.DictReader(io.StringIO(text)))

    assert parsed[0]["config"] == '{"account_id": "acc_123"}'


def test_snapshots_to_csv_pivots_breakdown_into_columns():
    snapshots = [
        {"id": 1, "snapshot_date": "2026-01-01", "total_assets": "1000.00",
         "total_liabilities": "0.00", "net_worth": "1000.00",
         "breakdown": {"account:Savings": 600.0, "conn:Trading212": 400.0}},
        {"id": 2, "snapshot_date": "2026-02-01", "total_assets": "1100.00",
         "total_liabilities": "0.00", "net_worth": "1100.00",
         "breakdown": {"account:Savings": 650.0, "conn:Coinbase": 450.0}},
    ]

    text = _snapshots_to_csv(snapshots)
    parsed = list(csv.DictReader(io.StringIO(text)))

    # Column order is first-seen across rows; later-only keys still get a column.
    assert parsed[0].keys() == {
        "id", "snapshot_date", "total_assets", "total_liabilities", "net_worth",
        "account:Savings", "conn:Trading212", "conn:Coinbase",
    }
    assert parsed[0]["account:Savings"] == "600.0"
    assert parsed[0]["conn:Coinbase"] == ""  # absent in row 1
    assert parsed[1]["conn:Trading212"] == ""  # absent in row 2
    assert parsed[1]["conn:Coinbase"] == "450.0"


def test_snapshots_to_csv_skips_underscore_prefixed_metadata_keys():
    """Backfilled snapshots carry a `_meta` entry in `breakdown` (e.g.
    {"reconstructed": True}) alongside the real source amounts. It must not
    become its own spreadsheet column."""
    snapshots = [
        {"id": 1, "snapshot_date": "2026-01-01", "total_assets": "100.00",
         "total_liabilities": "0.00", "net_worth": "100.00",
         "breakdown": {"account:Savings": 100.0, "_meta": {"reconstructed": True}}},
    ]

    text = _snapshots_to_csv(snapshots)
    parsed = list(csv.DictReader(io.StringIO(text)))

    assert "_meta" not in parsed[0]
    assert parsed[0]["account:Savings"] == "100.0"
