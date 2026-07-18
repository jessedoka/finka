"""Projected value of long-term savings.

Projects each source forward with monthly contributions and compound growth,
minus an annual charge. Sources:
  - manual accounts (active) -> balance + their monthly_contribution / annual_charge
    / growth_rate columns
  - Monzo pots -> current pots value + config-driven contribution / growth
  - other providers (Trading212, Coinbase) -> current value, held flat (0 growth,
    0 contribution) so the projected net-worth total stays complete

The per-source monthly recurrence is:
    value = value * (1 + growth_rate/12) + monthly_contribution - annual_charge/12
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.account import Account
from services.net_worth_service import NetWorthService


@dataclass
class Source:
    label: str
    value: float
    monthly_contribution: float
    annual_charge: float
    growth_rate: float


def project_series(sources: list[Source], years: int, start: date) -> dict:
    """Yearly projected points for the summed sources over `years`.

    Returns { series: [{date, value, breakdown}], contributed, growth }.
    Point 0 is today; then one point per year.
    """
    values = {s.label: s.value for s in sources}
    start_total = sum(values.values())
    contributed = 0.0

    series = [
        {
            "date": start.isoformat(),
            "value": round(start_total, 2),
            "breakdown": {k: round(v, 2) for k, v in values.items()},
        }
    ]

    for year in range(1, years + 1):
        for _ in range(12):
            for s in sources:
                monthly_rate = s.growth_rate / 12
                values[s.label] = (
                    values[s.label] * (1 + monthly_rate)
                    + s.monthly_contribution
                    - s.annual_charge / 12
                )
                contributed += s.monthly_contribution
        total = sum(values.values())
        series.append(
            {
                "date": date(start.year + year, start.month, 1).isoformat(),
                "value": round(total, 2),
                "breakdown": {k: round(v, 2) for k, v in values.items()},
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
                    label=a.name,
                    value=float(a.balance),
                    monthly_contribution=float(a.monthly_contribution),
                    annual_charge=float(a.annual_charge),
                    growth_rate=float(a.growth_rate),
                )
            )

        # Live providers: current values from the breakdown (snapshot providers +
        # live accounts). Skip the account:* entries — accounts are handled above.
        breakdown = await NetWorthService(self.db).get_current_breakdown(user_id)
        for key, value in breakdown["breakdown"].items():
            if key in manual_labels:
                continue
            if key == "monzo":
                sources.append(
                    Source(
                        label="Monzo pots",
                        value=float(value),
                        monthly_contribution=settings.monzo_pots_monthly_contribution,
                        annual_charge=0.0,
                        growth_rate=settings.monzo_pots_growth_rate,
                    )
                )
            else:
                # Trading212 / Coinbase / anything else: held flat.
                label = {"trading212": "Trading212", "coinbase": "Coinbase"}.get(key, key)
                sources.append(
                    Source(label=label, value=float(value), monthly_contribution=0.0,
                           annual_charge=0.0, growth_rate=0.0)
                )

        return sources

    async def project(self, user_id: UUID, years: int) -> dict:
        sources = await self._sources(user_id)
        return project_series(sources, years, date.today())
