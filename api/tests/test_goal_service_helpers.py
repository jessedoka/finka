"""Funding maths in the goal service: partial slices cap at the live value,
missing sources count zero, and the run-rate stays honest when history is thin.

All pure (no DB): _counted / _funded are free functions, and _progress / _run_rate
only read the objects passed in, so GoalService(db=None) is fine here.
"""

from datetime import date, timedelta
from decimal import Decimal

from models.goal import Goal, GoalAllocation
from services.goal_service import GoalService, _counted, _funded


def _alloc(source_key: str, allocated: str | None) -> GoalAllocation:
    return GoalAllocation(
        source_key=source_key,
        allocated_amount=Decimal(allocated) if allocated is not None else None,
    )


def test_whole_source_counts_full_live_value():
    a = _alloc("account:Savings", None)
    assert _counted(a, 8000.0) == 8000.0


def test_partial_slice_capped_at_live_value():
    # £5,200 earmarked but the pot now holds only £4,000 -> counts £4,000.
    a = _alloc("account:Savings", "5200")
    assert _counted(a, 4000.0) == 4000.0


def test_partial_slice_below_live_value_counts_the_slice():
    # £5,200 earmarked, pot holds £8,000 -> only the slice counts.
    a = _alloc("account:Savings", "5200")
    assert _counted(a, 8000.0) == 5200.0


def test_missing_source_key_counts_zero():
    allocs = [_alloc("conn:Deleted Pot", None), _alloc("account:Savings", "1000")]
    breakdown = {"account:Savings": 1000.0}  # no key for the deleted pot
    assert _funded(allocs, breakdown) == 1000.0


def _goal(target: str, target_date: date | None, allocs: list[GoalAllocation]) -> Goal:
    g = Goal(
        name="Trip",
        target_amount=Decimal(target),
        target_date=target_date,
        currency="GBP",
        ring_fenced=False,
    )
    g.allocations = allocs
    return g


def test_progress_remaining_pct_and_required_monthly():
    svc = GoalService(db=None)  # type: ignore[arg-type]
    goal = _goal("22000", date.today() + timedelta(days=304), [_alloc("account:Savings", None)])
    p = svc._progress(goal, {"account:Savings": 8000.0})

    assert p["funded"] == 8000.0
    assert p["remaining"] == 14000.0
    assert p["pct"] == round(8000 / 22000, 4)
    assert p["reached"] is False
    # ~10 months to go, £14k remaining -> ~£1.4k/month required.
    assert 1350 < p["required_monthly"] < 1450


def test_progress_reached_clamps_remaining_to_zero():
    svc = GoalService(db=None)  # type: ignore[arg-type]
    goal = _goal("1000", None, [_alloc("account:Savings", None)])
    p = svc._progress(goal, {"account:Savings": 1200.0})
    assert p["reached"] is True
    assert p["remaining"] == 0.0
    assert p["required_monthly"] is None  # no deadline


def test_run_rate_on_track_vs_behind():
    svc = GoalService(db=None)  # type: ignore[arg-type]
    series = [
        {"date": (date.today() - timedelta(days=60)).isoformat(), "funded": 6000.0},
        {"date": date.today().isoformat(), "funded": 9000.0},
    ]  # +£3000 over ~2 months -> ~£1500/month actual
    on_progress = {"required_monthly": 1000.0, "reached": False}
    actual, on_track = svc._run_rate(series, on_progress)
    assert 1400 < actual < 1600
    assert on_track is True

    behind = {"required_monthly": 2000.0, "reached": False}
    _, on_track_behind = svc._run_rate(series, behind)
    assert on_track_behind is False


def test_run_rate_insufficient_history_is_unknown():
    svc = GoalService(db=None)  # type: ignore[arg-type]
    one_point = [{"date": date.today().isoformat(), "funded": 5000.0}]
    assert svc._run_rate(one_point, {"required_monthly": 100.0, "reached": False}) == (None, None)
