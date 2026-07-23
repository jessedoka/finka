from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class GoalCreate(BaseModel):
    name: str
    target_amount: Decimal = Field(gt=0)
    target_date: date | None = None
    currency: str = "GBP"
    ring_fenced: bool = False
    notes: str | None = None


class GoalUpdate(BaseModel):
    """All optional — PATCH only touches provided fields. Send target_date/notes
    as null to clear them (exclude_unset distinguishes 'clear' from 'leave alone')."""
    name: str | None = None
    target_amount: Decimal | None = Field(default=None, gt=0)
    target_date: date | None = None
    currency: str | None = None
    ring_fenced: bool | None = None
    notes: str | None = None


class AllocationCreate(BaseModel):
    # Breakdown identity: "account:{name}" or "conn:{label}".
    source_key: str
    # null => the source's whole live value counts; a value => just that slice.
    allocated_amount: Decimal | None = Field(default=None, gt=0)


# --- responses (mirror GoalService progress dicts; keep in sync) ---------------


class AllocationProgress(BaseModel):
    id: int
    source_key: str
    allocated_amount: float | None
    counted: float


class GoalProgress(BaseModel):
    id: int
    name: str
    currency: str
    ring_fenced: bool
    target: float
    funded: float
    remaining: float
    pct: float | None
    reached: bool
    target_date: str | None
    days_remaining: int | None
    months_remaining: float | None
    required_monthly: float | None
    overdue: bool
    allocations: list[AllocationProgress]


class GoalSeriesPoint(BaseModel):
    date: str
    funded: float


class GoalDetail(GoalProgress):
    series: list[GoalSeriesPoint]
    actual_monthly: float | None
    on_track: bool | None
