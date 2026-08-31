"""project_series: compounding math, and label collisions must sum, not drop."""

from datetime import date

from services.projection_service import Source, project_series


def test_flat_source_holds_value_with_no_growth_or_contribution():
    sources = [Source(key="a", label="Savings", value=1000.0,
                       monthly_contribution=0.0, annual_charge=0.0, growth_rate=0.0)]
    result = project_series(sources, years=2, start=date(2026, 1, 1))
    assert result["series"][0]["value"] == 1000.0
    assert result["series"][-1]["value"] == 1000.0
    assert result["contributed"] == 0.0
    assert result["growth"] == 0.0


def test_monthly_compounding_matches_manual_calculation():
    sources = [Source(key="a", label="ISA", value=1000.0,
                       monthly_contribution=100.0, annual_charge=0.0, growth_rate=0.12)]
    result = project_series(sources, years=1, start=date(2026, 1, 1))

    expected = 1000.0
    for _ in range(12):
        expected = expected * (1 + 0.12 / 12) + 100.0

    assert result["series"][-1]["value"] == round(expected, 2)
    assert result["contributed"] == 1200.0


def test_duplicate_labels_are_summed_not_dropped():
    """Two sources sharing a display label (e.g. two accounts both named
    "Pension") must both contribute to the total instead of one silently
    overwriting the other in the running-value dict."""
    sources = [
        Source(key="account:1", label="Pension", value=10_000.0,
               monthly_contribution=0.0, annual_charge=0.0, growth_rate=0.0),
        Source(key="account:2", label="Pension", value=5_000.0,
               monthly_contribution=0.0, annual_charge=0.0, growth_rate=0.0),
    ]
    result = project_series(sources, years=1, start=date(2026, 1, 1))

    assert result["series"][0]["value"] == 15_000.0
    assert result["series"][0]["breakdown"] == {"Pension": 15_000.0}
    assert result["series"][-1]["value"] == 15_000.0


def test_duplicate_labels_compound_independently():
    """Colliding labels must not blend into a single growth track — each
    source keeps its own rate/contribution and the breakdown sums per label."""
    sources = [
        Source(key="account:1", label="Pension", value=1000.0,
               monthly_contribution=0.0, annual_charge=0.0, growth_rate=0.12),
        Source(key="account:2", label="Pension", value=1000.0,
               monthly_contribution=0.0, annual_charge=0.0, growth_rate=0.0),
    ]
    result = project_series(sources, years=1, start=date(2026, 1, 1))

    grown = 1000.0
    for _ in range(12):
        grown = grown * (1 + 0.12 / 12)
    expected_total = round(grown, 2) + 1000.0

    assert result["series"][-1]["value"] == round(expected_total, 2)

# --- goal outflows (Spend) ---------------------------------------------------


def test_spend_reduces_net_worth_and_stops_compounding():
    from services.projection_service import Spend

    sources = [Source(key="a", label="Savings", value=1000.0,
                      monthly_contribution=0.0, annual_charge=0.0, growth_rate=0.0)]
    spends = [Spend(month=6, date=date(2026, 7, 1), amount=200.0, name="Trip")]
    result = project_series(sources, years=1, start=date(2026, 1, 1), spends=spends)

    # £1000 flat, spend £200 at month 6 -> ends at £800.
    assert result["series"][-1]["value"] == 800.0
    assert result["spent"] == 200.0
    assert result["growth"] == 0.0  # spend is not negative growth
    assert len(result["events"]) == 1
    ev = result["events"][0]
    assert ev["name"] == "Trip"
    assert ev["drop"] == 200.0
    assert ev["value_before"] == 1000.0
    assert ev["value_after"] == 800.0


def test_spend_beyond_horizon_never_fires():
    from services.projection_service import Spend

    sources = [Source(key="a", label="Savings", value=1000.0,
                      monthly_contribution=0.0, annual_charge=0.0, growth_rate=0.0)]
    spends = [Spend(month=99, date=date(2034, 1, 1), amount=200.0, name="Far")]
    result = project_series(sources, years=1, start=date(2026, 1, 1), spends=spends)
    assert result["series"][-1]["value"] == 1000.0
    assert result["events"] == []


def test_spend_larger_than_net_worth_floors_at_zero():
    from services.projection_service import Spend

    sources = [Source(key="a", label="Savings", value=500.0,
                      monthly_contribution=0.0, annual_charge=0.0, growth_rate=0.0)]
    spends = [Spend(month=3, date=date(2026, 4, 1), amount=900.0, name="Overspend")]
    result = project_series(sources, years=1, start=date(2026, 1, 1), spends=spends)
    assert result["series"][-1]["value"] == 0.0
    assert result["spent"] == 500.0  # only what was there actually leaves
