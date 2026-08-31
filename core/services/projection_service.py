"""Projected value of long-term savings.

Projects each source forward with monthly contributions and compound growth,
minus an annual charge. Sources:
  - manual accounts (active) -> balance + their monthly_contribution / annual_charge
    / growth_rate columns
  - connections (conn:*) -> current value + any monthly_contribution / growth_rate
    set in the connection's config; absent => held flat (0 growth, 0 contribution)
    so the projected net-worth total stays complete

The per-source monthly recurrence is:
    value = value * (1 + growth_rate/12) + monthly_contribution - annual_charge/12
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.account import Account
from models.connection import Connection
from models.goal import Goal
from services.net_worth_service import NetWorthService


@dataclass
class Source:
    key: str  # stable, unique identity (e.g. "account:{id}") — never used for display
    label: str  # display name; may collide across sources (user-supplied, not unique)
    value: float
    monthly_contribution: float
    annual_charge: float
    growth_rate: float


@dataclass
class Spend:
    """A one-time planned outflow — a dated goal's cost leaving net worth."""

    month: int  # months from start (1-based) when the outflow lands
    date: date
    amount: float
    name: str


def project_series(
    sources: list[Source], years: int, start: date, spends: list[Spend] | None = None
) -> dict:
    """Yearly projected points for the summed sources over `years`.

    Returns { series: [{date, value, breakdown}], contributed, growth, spent, events }.
    Point 0 is today; then one point per year.

    Goal outflows: each Spend is a one-time withdrawal at its month — the money
    leaves net worth (spent on the trip / deposit / …) and stops compounding, so
    the line dips at the goal date and continues lower. The drop is spread
    proportionally across the sources present at that moment (we don't track which
    source funds which goal here — this is a whole-net-worth forecast). Each spend
    adds a peak point just before and a trough point at the date, so the dip reads
    as a sharp step rather than a slow slide; `events` describes each drop.

    Running values are keyed by `Source.key`, not `label`: labels are
    user-supplied and can collide (two accounts named "Pension"), and keying
    by label would silently drop one source instead of summing it. The
    breakdown shown to the caller groups by label for display.
    """
    by_month: dict[int, list[Spend]] = {}
    for sp in spends or []:
        by_month.setdefault(sp.month, []).append(sp)

    values = {s.key: s.value for s in sources}
    contributed = 0.0
    spent = 0.0
    events: list[dict] = []

    def breakdown_of(values: dict[str, float]) -> dict[str, float]:
        by_label: dict[str, float] = {}
        for s in sources:
            by_label[s.label] = by_label.get(s.label, 0.0) + values[s.key]
        return {k: round(v, 2) for k, v in by_label.items()}

    start_total = sum(values.values())
    series = [
        {
            "date": start.isoformat(),
            "value": round(start_total, 2),
            "breakdown": breakdown_of(values),
        }
    ]

    month = 0
    for year in range(1, years + 1):
        for _ in range(12):
            month += 1
            for s in sources:
                monthly_rate = s.growth_rate / 12
                values[s.key] = (
                    values[s.key] * (1 + monthly_rate)
                    + s.monthly_contribution
                    - s.annual_charge / 12
                )
                contributed += s.monthly_contribution

            for sp in by_month.get(month, []):
                before = sum(values.values())
                # Peak point just before the outflow so the drop renders vertically.
                series.append(
                    {
                        "date": sp.date.isoformat(),
                        "value": round(before, 2),
                        "breakdown": breakdown_of(values),
                    }
                )
                factor = max(0.0, (before - sp.amount) / before) if before > 0 else 0.0
                for k in values:
                    values[k] *= factor
                after = sum(values.values())
                spent += before - after
                events.append(
                    {
                        "date": sp.date.isoformat(),
                        "name": sp.name,
                        "amount": round(sp.amount, 2),
                        "value_before": round(before, 2),
                        "value_after": round(after, 2),
                        "drop": round(before - after, 2),
                    }
                )
                series.append(
                    {
                        "date": sp.date.isoformat(),
                        "value": round(after, 2),
                        "breakdown": breakdown_of(values),
                        "event": sp.name,
                    }
                )

        total = sum(values.values())
        series.append(
            {
                "date": date(start.year + year, start.month, 1).isoformat(),
                "value": round(total, 2),
                "breakdown": breakdown_of(values),
            }
        )

    end_total = sum(values.values())
    # Spends are neither contributions nor negative growth; add them back so the
    # growth figure stays "pure" investment return: end = start + contributed + growth - spent.
    growth = end_total - start_total - contributed + spent
    return {
        "years": years,
        "series": series,
        "contributed": round(contributed, 2),
        "growth": round(growth, 2),
        "spent": round(spent, 2),
        "events": events,
    }


class ProjectionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _sources(self, user_id: UUID) -> list[Source]:
        sources: list[Source] = []

        # Manual accounts (active) — full projection params from their columns.
        accounts = await self.db.scalars(
            select(Account).where(Account.user_id == user_id, Account.is_active.is_(True))
        )
        manual_labels: set[str] = set()
        for a in accounts:
            manual_labels.add(f"account:{a.name}")
            sources.append(
                Source(
                    key=f"account:{a.id}",
                    label=a.name,
                    value=float(a.balance),
                    monthly_contribution=float(a.monthly_contribution),
                    annual_charge=float(a.annual_charge),
                    growth_rate=float(a.growth_rate),
                )
            )

        # Projection knobs per connection, keyed conn:{label}. A connection may
        # set monthly_contribution / growth_rate in its config (e.g. Monzo pots
        # you keep topping up); anything unset defaults to held-flat.
        conn_cfg: dict[str, dict] = {}
        connections = await self.db.scalars(
            select(Connection).where(
                Connection.user_id == user_id, Connection.is_active.is_(True)
            )
        )
        for conn in connections:
            conn_cfg[f"conn:{conn.label}"] = conn.config or {}

        # Live sources: current values from the breakdown (snapshot connections +
        # live accounts). Skip the account:* entries — accounts are handled above.
        breakdown = await NetWorthService(self.db).get_current_breakdown(user_id)
        for key, value in breakdown["breakdown"].items():
            if key in manual_labels:
                continue
            cfg = conn_cfg.get(key, {})
            label = key[len("conn:"):] if key.startswith("conn:") else key
            sources.append(
                Source(
                    key=key,
                    label=label,
                    value=float(value),
                    monthly_contribution=float(cfg.get("monthly_contribution", 0.0) or 0.0),
                    annual_charge=float(cfg.get("annual_charge", 0.0) or 0.0),
                    growth_rate=float(cfg.get("growth_rate", 0.0) or 0.0),
                )
            )

        return sources

    async def _spends(self, user_id: UUID, start: date, years: int) -> list[Spend]:
        """Dated goals become planned outflows in the projection.

        Ring-fenced goals are excluded: ring-fencing means "reserved, do not spend"
        (e.g. a proof-of-funds floor), so it should NOT dip the projection. Only
        goals with a future date inside the horizon are spends; the amount is the
        goal's target (its planned cost), independent of how much is funded today.
        """
        horizon_months = years * 12
        goals = await self.db.scalars(
            select(Goal).where(
                Goal.user_id == user_id,
                Goal.ring_fenced.is_(False),
                Goal.target_date.is_not(None),
            )
        )
        spends: list[Spend] = []
        for g in goals:
            month = (g.target_date.year - start.year) * 12 + (g.target_date.month - start.month)
            if month < 1 or month > horizon_months:
                continue
            spends.append(
                Spend(month=month, date=g.target_date, amount=float(g.target_amount), name=g.name)
            )
        return spends

    async def project(self, user_id: UUID, years: int) -> dict:
        start = date.today()
        sources = await self._sources(user_id)
        spends = await self._spends(user_id, start, years)
        return project_series(sources, years, start, spends)
