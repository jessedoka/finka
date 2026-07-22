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
from services.net_worth_service import NetWorthService


@dataclass
class Source:
    key: str  # stable, unique identity (e.g. "account:{id}") — never used for display
    label: str  # display name; may collide across sources (user-supplied, not unique)
    value: float
    monthly_contribution: float
    annual_charge: float
    growth_rate: float


def project_series(sources: list[Source], years: int, start: date) -> dict:
    """Yearly projected points for the summed sources over `years`.

    Returns { series: [{date, value, breakdown}], contributed, growth }.
    Point 0 is today; then one point per year.

    Running values are keyed by `Source.key`, not `label`: labels are
    user-supplied and can collide (two accounts named "Pension"), and keying
    by label would silently drop one source instead of summing it. The
    breakdown shown to the caller groups by label for display.
    """
    values = {s.key: s.value for s in sources}
    contributed = 0.0

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

    for year in range(1, years + 1):
        for _ in range(12):
            for s in sources:
                monthly_rate = s.growth_rate / 12
                values[s.key] = (
                    values[s.key] * (1 + monthly_rate)
                    + s.monthly_contribution
                    - s.annual_charge / 12
                )
                contributed += s.monthly_contribution
        total = sum(values.values())
        series.append(
            {
                "date": date(start.year + year, start.month, 1).isoformat(),
                "value": round(total, 2),
                "breakdown": breakdown_of(values),
            }
        )

    end_total = series[-1]["value"]
    growth = end_total - start_total - contributed
    return {
        "years": years,
        "series": series,
        "contributed": round(contributed, 2),
        "growth": round(growth, 2),
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

    async def project(self, user_id: UUID, years: int) -> dict:
        sources = await self._sources(user_id)
        return project_series(sources, years, date.today())
