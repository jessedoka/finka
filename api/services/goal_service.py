"""Goals: how funded a target is, and its funding curve over time.

A goal is funded by *earmarking* real sources (GoalAllocation.source_key, a
breakdown key like "account:Savings" / "conn:Monzo Travel"). Nothing is stored
separately — funded value is read straight off the net-worth breakdown, so it
stays honest and the history chart falls out of the daily snapshots we already
keep.

Two rules the whole file turns on:
  * Cap partial slices at the live value. An allocation of £5,200 from a pot that
    now holds only £4,000 counts £4,000 — a source dropping below its earmarked
    slice shows the goal as under-funded rather than pretending it's covered.
    (Matters most for a ring-fenced proof-of-funds floor.)
  * A missing source key counts 0. Deleted / renamed / errored source => that
    allocation simply contributes nothing, never crashes the calc.
"""

from datetime import date
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.goal import Goal, GoalAllocation
from models.net_worth_snapshot import NetWorthSnapshot
from schemas.goal import AllocationCreate, GoalCreate, GoalUpdate
from services.net_worth_service import NetWorthService

# Average days per month — turns a deadline in days into months for run-rates.
_DAYS_PER_MONTH = 30.44
# Below this much elapsed history, an "actual monthly rate" is too noisy to report.
_MIN_MONTHS_FOR_RATE = 0.5


def _validate_source_key(source_key: str) -> None:
    """A source_key must name a breakdown line: 'account:{name}' or 'conn:{label}'.

    We don't require the source to exist right now — a temporarily-errored or
    not-yet-snapshotted source is legitimately earmarkable and just counts 0 until
    it reports — but the prefix has to be one the breakdown can ever produce.
    """
    if not (source_key.startswith("account:") or source_key.startswith("conn:")):
        raise HTTPException(
            status_code=400,
            detail="source_key must start with 'account:' or 'conn:'",
        )


def _counted(alloc: GoalAllocation, available: float) -> float:
    """This allocation's contribution: the whole source, or a slice capped at live value."""
    if alloc.allocated_amount is None:
        return available
    return min(float(alloc.allocated_amount), available)


def _funded(allocations: list[GoalAllocation], breakdown: dict[str, float]) -> float:
    """Sum every allocation against a breakdown (missing key => 0)."""
    return sum(_counted(a, breakdown.get(a.source_key, 0.0)) for a in allocations)


class GoalService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _get(self, user_id: UUID, goal_id: int) -> Goal | None:
        # populate_existing forces a refresh of the identity-mapped goal AND its
        # allocations collection. Without it, a read straight after a write in the
        # same request/session returns stale relationship state (e.g. a just-removed
        # allocation lingering), because commit doesn't expire loaded collections.
        return await self.db.scalar(
            select(Goal)
            .where(Goal.id == goal_id, Goal.user_id == user_id)
            .options(selectinload(Goal.allocations))
            .execution_options(populate_existing=True)
        )

    async def _all(self, user_id: UUID) -> list[Goal]:
        result = await self.db.execute(
            select(Goal)
            .where(Goal.user_id == user_id)
            .options(selectinload(Goal.allocations))
            .order_by(Goal.created_at)
        )
        return list(result.scalars().all())

    async def _get_owned(self, user_id: UUID, goal_id: int) -> Goal:
        goal = await self._get(user_id, goal_id)
        if goal is None:
            raise HTTPException(status_code=404, detail="Goal not found")
        return goal

    # --- writes ---------------------------------------------------------------

    async def create(self, user_id: UUID, data: GoalCreate) -> Goal:
        goal = Goal(
            user_id=user_id,
            name=data.name,
            target_amount=data.target_amount,
            target_date=data.target_date,
            currency=data.currency,
            ring_fenced=data.ring_fenced,
            notes=data.notes,
        )
        self.db.add(goal)
        await self.db.commit()
        return await self._get_owned(user_id, goal.id)

    async def update(self, user_id: UUID, goal_id: int, data: GoalUpdate) -> Goal:
        goal = await self._get_owned(user_id, goal_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(goal, field, value)
        await self.db.commit()
        return await self._get_owned(user_id, goal_id)

    async def delete(self, user_id: UUID, goal_id: int) -> None:
        goal = await self._get_owned(user_id, goal_id)
        await self.db.delete(goal)
        await self.db.commit()

    async def add_allocation(self, user_id: UUID, goal_id: int, data: AllocationCreate) -> Goal:
        goal = await self._get_owned(user_id, goal_id)
        _validate_source_key(data.source_key)
        if any(a.source_key == data.source_key for a in goal.allocations):
            raise HTTPException(
                status_code=409,
                detail=f"{data.source_key} is already earmarked to this goal",
            )
        self.db.add(
            GoalAllocation(
                goal_id=goal.id,
                source_key=data.source_key,
                allocated_amount=data.allocated_amount,
            )
        )
        await self.db.commit()
        return await self._get_owned(user_id, goal_id)

    async def remove_allocation(self, user_id: UUID, goal_id: int, allocation_id: int) -> Goal:
        goal = await self._get_owned(user_id, goal_id)
        alloc = next((a for a in goal.allocations if a.id == allocation_id), None)
        if alloc is None:
            raise HTTPException(status_code=404, detail="Allocation not found")
        await self.db.delete(alloc)
        await self.db.commit()
        return await self._get_owned(user_id, goal_id)

    def _progress(self, goal: Goal, breakdown: dict[str, float]) -> dict:
        """Funded / remaining / run-rate for one goal against a live breakdown."""
        target = float(goal.target_amount)
        funded = _funded(goal.allocations, breakdown)
        remaining = max(target - funded, 0.0)
        pct = (funded / target) if target > 0 else None

        days_remaining: int | None = None
        months_remaining: float | None = None
        required_monthly: float | None = None
        overdue = False
        if goal.target_date is not None:
            days_remaining = (goal.target_date - date.today()).days
            if days_remaining > 0:
                months_remaining = days_remaining / _DAYS_PER_MONTH
                required_monthly = remaining / months_remaining
            elif remaining > 0:
                # Deadline passed and still short of target.
                overdue = True

        return {
            "id": goal.id,
            "name": goal.name,
            "currency": goal.currency,
            "ring_fenced": goal.ring_fenced,
            "target": round(target, 2),
            "funded": round(funded, 2),
            "remaining": round(remaining, 2),
            "pct": round(pct, 4) if pct is not None else None,
            "reached": funded >= target,
            "target_date": goal.target_date.isoformat() if goal.target_date else None,
            "days_remaining": days_remaining,
            "months_remaining": round(months_remaining, 1) if months_remaining else None,
            "required_monthly": round(required_monthly, 2) if required_monthly is not None else None,
            "overdue": overdue,
            "allocations": [
                {
                    "id": a.id,
                    "source_key": a.source_key,
                    "allocated_amount": float(a.allocated_amount) if a.allocated_amount is not None else None,
                    "counted": round(_counted(a, breakdown.get(a.source_key, 0.0)), 2),
                }
                for a in goal.allocations
            ],
        }

    async def list_with_progress(self, user_id: UUID) -> list[dict]:
        """Every goal with its funded/remaining/run-rate, against one live breakdown read."""
        breakdown = (await NetWorthService(self.db).get_current_breakdown(user_id))["breakdown"]
        goals = await self._all(user_id)
        return [self._progress(g, breakdown) for g in goals]

    async def detail(self, user_id: UUID, goal_id: int) -> dict | None:
        """One goal's progress plus its funding-over-time series and inferred run-rate."""
        goal = await self._get(user_id, goal_id)
        if goal is None:
            return None
        breakdown = (await NetWorthService(self.db).get_current_breakdown(user_id))["breakdown"]
        progress = self._progress(goal, breakdown)
        series = await self._funding_series(user_id, goal)
        progress["series"] = series
        progress["actual_monthly"], progress["on_track"] = self._run_rate(series, progress)
        return progress

    async def _funding_series(self, user_id: UUID, goal: Goal) -> list[dict]:
        """Funded value at each past snapshot — the goal's funding curve, for free.

        Each snapshot stored its own per-source breakdown, so we replay the same
        capped-sum against history. Oldest first.
        """
        result = await self.db.execute(
            select(NetWorthSnapshot)
            .where(NetWorthSnapshot.user_id == user_id)
            .order_by(NetWorthSnapshot.snapshot_date)
        )
        points: list[dict] = []
        for snap in result.scalars().all():
            breakdown = snap.breakdown or {}
            points.append(
                {
                    "date": snap.snapshot_date.isoformat(),
                    "funded": round(_funded(goal.allocations, breakdown), 2),
                }
            )
        return points

    def _run_rate(self, series: list[dict], progress: dict) -> tuple[float | None, bool | None]:
        """Actual £/month accrued (first→last snapshot) and whether it beats the required rate.

        Returns (actual_monthly, on_track). Both None when there isn't enough
        history to say honestly, or when the goal has no deadline. `on_track` is
        left None (not False) so the UI can show "not enough data yet" rather than
        a misleading ✗ on a young goal.
        """
        if len(series) < 2:
            return None, None
        first, last = series[0], series[-1]
        elapsed_days = (date.fromisoformat(last["date"]) - date.fromisoformat(first["date"])).days
        elapsed_months = elapsed_days / _DAYS_PER_MONTH
        if elapsed_months < _MIN_MONTHS_FOR_RATE:
            return None, None
        actual_monthly = round((last["funded"] - first["funded"]) / elapsed_months, 2)

        required = progress.get("required_monthly")
        if required is None:
            # No deadline (or already reached / overdue) => no rate to beat.
            on_track = None if not progress["reached"] else True
        else:
            on_track = actual_monthly >= required
        return actual_monthly, on_track
