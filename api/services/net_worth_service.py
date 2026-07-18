"""Net-worth snapshots: record a point-in-time asset value, read the series.

WHY THIS EXISTS: Trading212 (like most providers) has no "portfolio value over
time" endpoint. The history chart is therefore built from snapshots WE record —
one row per day — that accumulate going forward. Day one is a single point; it
becomes a real line over time.

Phase 0 scope: only Trading212 is connected, so total_assets = the T212 account
`total`. When Monzo/Coinbase/etc. land, sum their balances here instead and put
the per-source split in `breakdown`.
"""

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from integrations.trading212 import Trading212Client
from models.net_worth_snapshot import NetWorthSnapshot


class NetWorthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def record_snapshot(self, user_id: UUID) -> NetWorthSnapshot:
        """Fetch today's T212 value and upsert one snapshot for today.

        Upsert (not insert) so re-running on the same day overwrites rather than
        colliding with the uq_networth_user_date unique constraint.
        """
        cash = await Trading212Client().fetch_cash()
        total = Decimal(str(cash["total"]))

        today = date.today()
        existing = await self.db.scalar(
            select(NetWorthSnapshot).where(
                NetWorthSnapshot.user_id == user_id,
                NetWorthSnapshot.snapshot_date == today,
            )
        )

        breakdown = {"trading212": float(total)}
        if existing is not None:
            existing.total_assets = total
            existing.net_worth = total
            existing.breakdown = breakdown
            snapshot = existing
        else:
            snapshot = NetWorthSnapshot(
                user_id=user_id,
                snapshot_date=today,
                total_assets=total,
                total_liabilities=Decimal("0.00"),
                net_worth=total,
                breakdown=breakdown,
            )
            self.db.add(snapshot)

        await self.db.commit()
        await self.db.refresh(snapshot)
        return snapshot

    async def get_series(self, user_id: UUID) -> list[NetWorthSnapshot]:
        """All snapshots for the user, oldest first — the chart's data source."""
        result = await self.db.execute(
            select(NetWorthSnapshot)
            .where(NetWorthSnapshot.user_id == user_id)
            .order_by(NetWorthSnapshot.snapshot_date)
        )
        return list(result.scalars().all())
