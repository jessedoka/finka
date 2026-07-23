"""The third 'committed' bucket: ring-fenced goals carve their earmarked slice
out of spendable, honouring the partial-slice cap and long-term precedence.

Pure test of _committed_slices — no DB — using fabricated Goal/GoalAllocation
objects, same style as the goal-service helper tests.
"""

from decimal import Decimal

from models.goal import Goal, GoalAllocation
from services.net_worth_service import _committed_slices


def _goal(*allocs: GoalAllocation) -> Goal:
    g = Goal(name="Reserve", target_amount=Decimal("1"), ring_fenced=True)
    g.allocations = list(allocs)
    return g


def _alloc(source_key: str, allocated: str | None) -> GoalAllocation:
    return GoalAllocation(
        source_key=source_key,
        allocated_amount=Decimal(allocated) if allocated is not None else None,
    )


def test_partial_slice_only_carves_the_slice():
    # £5,200 ring-fenced out of an £8,000 pot -> £5,200 committed, £2,800 stays spendable.
    goal = _goal(_alloc("account:Savings", "5200"))
    committed = _committed_slices([goal], {"account:Savings": 8000.0}, [])
    assert committed == {"account:Savings": 5200.0}


def test_whole_source_commits_full_value():
    goal = _goal(_alloc("conn:Travel Pot", None))
    committed = _committed_slices([goal], {"conn:Travel Pot": 1500.0}, [])
    assert committed == {"conn:Travel Pot": 1500.0}


def test_slice_capped_at_live_value():
    # Earmarked more than the pot now holds -> committed capped at live value.
    goal = _goal(_alloc("account:Savings", "5200"))
    committed = _committed_slices([goal], {"account:Savings": 4000.0}, [])
    assert committed == {"account:Savings": 4000.0}


def test_long_term_source_is_never_committed():
    goal = _goal(_alloc("account:Pension", None))
    committed = _committed_slices([goal], {"account:Pension": 20000.0}, ["account:Pension"])
    assert committed == {}


def test_missing_source_contributes_nothing():
    goal = _goal(_alloc("conn:Deleted", "1000"))
    committed = _committed_slices([goal], {"account:Savings": 500.0}, [])
    assert committed == {}


def test_cumulative_commit_never_exceeds_live_value():
    # Two goals each earmarking a slice of the same £8,000 pot; total can't exceed £8,000.
    g1 = _goal(_alloc("account:Savings", "5200"))
    g2 = _goal(_alloc("account:Savings", "5200"))
    committed = _committed_slices([g1, g2], {"account:Savings": 8000.0}, [])
    assert committed == {"account:Savings": 8000.0}


def test_non_ring_fenced_goals_are_the_callers_job():
    # Helper trusts the caller to pass only ring-fenced goals; it commits whatever
    # it's given. (get_current_breakdown filters ring_fenced in the query.)
    goal = _goal(_alloc("account:Savings", "100"))
    goal.ring_fenced = False
    committed = _committed_slices([goal], {"account:Savings": 8000.0}, [])
    assert committed == {"account:Savings": 100.0}
