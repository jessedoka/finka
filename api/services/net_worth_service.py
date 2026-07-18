"""Net-worth snapshots: record a point-in-time asset value, read the series.

WHY THIS EXISTS: Trading212 (like most providers) has no "portfolio value over
time" endpoint. The history chart is therefore built from snapshots WE record —
one row per day — that accumulate going forward. Day one is a single point; it
becomes a real line over time.

Sources are aggregated in `_collect_balances`: each connected provider
(Trading212, Coinbase, Monzo) plus any active manual Account rows contributes a
GBP figure. total_assets is their sum; the per-source split is stored in
`breakdown`. A provider that isn't configured is skipped; one that errors is
logged and contributes 0 rather than sinking the whole snapshot.
"""

import logging
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from integrations.coinbase import CoinbaseClient, CoinbaseError
from integrations.monzo import MonzoClient, MonzoError
from integrations.trading212 import Trading212Client, Trading212Error
from models.account import Account
from models.net_worth_snapshot import NetWorthSnapshot

logger = logging.getLogger(__name__)


class NetWorthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _collect_balances(self, user_id: UUID) -> dict[str, Decimal]:
        """One GBP figure per connected source. Missing sources are omitted."""
        breakdown: dict[str, Decimal] = {}

        # Trading212 — the only source that must be present (Phase 0 baseline).
        try:
            cash = await Trading212Client().fetch_cash()
            breakdown["trading212"] = Decimal(str(cash["total"]))
        except (Trading212Error, KeyError) as e:
            logger.warning("Trading212 balance unavailable: %s", e)

        coinbase = CoinbaseClient()
        if coinbase.configured:
            try:
                breakdown["coinbase"] = await coinbase.total_gbp()
            except CoinbaseError as e:
                logger.warning("Coinbase balance unavailable: %s", e)

        monzo = MonzoClient()
        if monzo.configured:
            try:
                breakdown["monzo"] = await monzo.total_gbp()
            except MonzoError as e:
                logger.warning("Monzo balance unavailable: %s", e)

        # Manual accounts (Peoples Pension, Tembo, ...): balances the user keeps
        # up to date by hand. Grouped under the account name.
        accounts = await self.db.scalars(
            select(Account).where(Account.user_id == user_id, Account.is_active.is_(True))
        )
        for acct in accounts:
            key = f"account:{acct.name}"
            breakdown[key] = breakdown.get(key, Decimal("0")) + Decimal(str(acct.balance))

        return breakdown

    async def record_snapshot(self, user_id: UUID) -> NetWorthSnapshot:
        """Aggregate every connected source and upsert one snapshot for today.

        Upsert (not insert) so re-running on the same day overwrites rather than
        colliding with the uq_networth_user_date unique constraint.
        """
        balances = await self._collect_balances(user_id)
        total = sum(balances.values(), Decimal("0"))
        breakdown = {k: float(v) for k, v in balances.items()}

        today = date.today()
        existing = await self.db.scalar(
            select(NetWorthSnapshot).where(
                NetWorthSnapshot.user_id == user_id,
                NetWorthSnapshot.snapshot_date == today,
            )
        )

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

    async def get_latest(self, user_id: UUID) -> NetWorthSnapshot | None:
        """Most recent snapshot — its `breakdown` is the per-source split."""
        return await self.db.scalar(
            select(NetWorthSnapshot)
            .where(NetWorthSnapshot.user_id == user_id)
            .order_by(NetWorthSnapshot.snapshot_date.desc())
            .limit(1)
        )

    async def get_current_breakdown(self, user_id: UUID) -> dict:
        """Live per-source split for the dashboard.

        External providers (Trading212/Coinbase/Monzo) come from the latest
        snapshot — re-fetching them every request would hit rate limits. Manual
        accounts are cheap DB reads, so we take them LIVE: a balance you edit
        shows up immediately, without waiting for the next daily snapshot.
        """
        snapshot = await self.get_latest(user_id)
        # Keep only external-provider entries from the snapshot; drop its
        # point-in-time account:* rows so the live ones below replace them.
        breakdown: dict[str, float] = {}
        snapshot_date = None
        if snapshot is not None and snapshot.breakdown:
            breakdown = {
                k: v for k, v in snapshot.breakdown.items() if not k.startswith("account:")
            }
            snapshot_date = snapshot.snapshot_date.isoformat()

        long_term_keys: list[str] = []
        accounts = await self.db.scalars(
            select(Account).where(Account.user_id == user_id, Account.is_active.is_(True))
        )
        for acct in accounts:
            key = f"account:{acct.name}"
            breakdown[key] = breakdown.get(key, 0.0) + float(acct.balance)
            if acct.is_long_term:
                long_term_keys.append(key)

        net_worth = sum(breakdown.values())
        spendable = sum(v for k, v in breakdown.items() if k not in long_term_keys)

        return {
            "date": snapshot_date,
            "net_worth": net_worth,
            "spendable": spendable,
            "long_term_keys": long_term_keys,
            "breakdown": breakdown,
        }
