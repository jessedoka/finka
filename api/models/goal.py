import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, Numeric, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import Base

if TYPE_CHECKING:
    from .user import User


class Goal(Base):
    """A savings goal / sinking fund — a named target you fund over time.

    Agnostic by design: "Asia trip 2027", "house deposit", "emergency fund" are
    all the same shape. A goal is *funded by earmarking real sources* (accounts
    or connections) via GoalAllocation, so progress and the funding-over-time
    curve fall out of the existing daily snapshots — no separately-tracked figure
    to keep in sync.

    `ring_fenced` introduces a third money state beyond spendable/long-term:
    money that is still liquid and still in net worth, but committed and must-not
    -spend (e.g. a WHV proof-of-funds requirement). When set, the goal's earmarked
    source keys are carved out of the "spendable" split.
    """

    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    # Optional deadline. A goal without a date is just a target (no run-rate / ETA).
    target_date: Mapped[date | None] = mapped_column(Date)
    currency: Mapped[str] = mapped_column(String(3), default="GBP")
    # Carve earmarked funds out of "spendable" — committed but liquid money.
    ring_fenced: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    notes: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="goals")
    allocations: Mapped[list["GoalAllocation"]] = relationship(
        back_populates="goal", cascade="all, delete-orphan"
    )


class GoalAllocation(Base):
    """One earmarked source contributing to a goal.

    `source_key` is the *breakdown* identity — the same key the net-worth split and
    every snapshot use: "account:{name}" or "conn:{label}". Earmarking a manual
    account and a live Monzo pot therefore go through one uniform mechanism, funded
    value and the funding-over-time series both resolve by a plain dict lookup into
    the breakdown, and nothing provider-specific leaks in. Caveat: name/label is the
    app's source identity everywhere, so renaming a source breaks its allocation —
    an accepted trade-off, not a new one introduced here.

    `allocated_amount` is an optional partial slice: null means "the source's
    whole current value counts toward this goal"; a value means "only this much of
    it is earmarked" (e.g. £5,200 of a larger savings pot). Funded value is capped
    at the source's live value — see GoalService.

    Note: the breakdown sums same-named accounts into one key, so an allocation to
    "account:Pension" earmarks that combined line — consistent with what the
    dashboard and history chart already show.
    """

    __tablename__ = "goal_allocations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("goals.id", ondelete="CASCADE"))
    # "account:{name}" | "conn:{label}" — label/name up to 100 chars, plus prefix.
    source_key: Mapped[str] = mapped_column(String(150), nullable=False)
    allocated_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    goal: Mapped["Goal"] = relationship(back_populates="allocations")
