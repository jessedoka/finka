"""Net-worth snapshots: record a point-in-time asset value, read the series.

WHY THIS EXISTS: Trading212 (like most providers) has no "portfolio value over
time" endpoint. The history chart is therefore built from snapshots WE record —
one row per day — that accumulate going forward. Day one is a single point; it
becomes a real line over time.

Sources are aggregated in `_collect_balances`: each active user Connection
(Monzo, Trading212, Coinbase, or a generic HTTP endpoint) plus any active manual
Account rows contributes a GBP figure. total_assets is their sum; the per-source
split is stored in `breakdown`. A connection that errors is logged and
contributes 0 rather than sinking the whole snapshot.
"""

import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified

from integrations import registry
from integrations.registry import ProviderError
from models.account import Account
from models.connection import Connection
from models.goal import Goal
from models.net_worth_snapshot import NetWorthSnapshot

logger = logging.getLogger(__name__)


def _committed_slices(
    ring_fenced_goals: list["Goal"],
    breakdown: dict[str, float],
    long_term_keys: list[str],
) -> dict[str, float]:
    """Per-source committed amount from ring-fenced goals — the 'committed' bucket.

    Only the earmarked slice is committed (partial allocations honour the same
    cap as funding: min(allocated, live value)), the cumulative per source can
    never exceed that source's live value, long-term sources are excluded (a
    locked source is never 'committed'), and a source absent from the breakdown
    contributes nothing. Kept pure and free-standing so it's unit-testable
    without a DB — and the local `_counted` import breaks the goal_service cycle.
    """
    from services.goal_service import _counted

    committed_by_key: dict[str, float] = {}
    for goal in ring_fenced_goals:
        for alloc in goal.allocations:
            key = alloc.source_key
            if key in long_term_keys or key not in breakdown:
                continue
            available = breakdown[key]
            room = available - committed_by_key.get(key, 0.0)
            if room <= 0:  # source already fully committed by another allocation/goal
                continue
            committed_by_key[key] = committed_by_key.get(key, 0.0) + min(
                _counted(alloc, available), room
            )
    return committed_by_key


class NetWorthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _collect_balances(self, user_id: UUID) -> dict[str, Decimal]:
        """One GBP figure per active source. Failing sources are logged and skipped."""
        breakdown: dict[str, Decimal] = {}

        # Connections: each is one instance of a registry provider. The registry
        # maps provider + config -> a GBP figure, so we never name a provider here.
        connections = await self.db.scalars(
            select(Connection).where(
                Connection.user_id == user_id, Connection.is_active.is_(True)
            )
        )
        now = datetime.now(timezone.utc)
        for conn in connections:
            key = f"conn:{conn.label}"
            conn.last_synced_at = now
            try:
                spec = registry.get(conn.provider)
                value = await spec.fetch_gbp(conn.config or {})
                breakdown[key] = breakdown.get(key, Decimal("0")) + value
                conn.last_status = "ok"
                conn.last_error = None
                conn.last_value = value
                # A provider may rotate credentials in-place (e.g. Monzo OAuth
                # refresh tokens). Flag the JSON column so the new tokens persist.
                flag_modified(conn, "config")
            except ProviderError as e:
                # An active source that fails contributes 0 rather than sinking the
                # whole snapshot; the health fields let the UI surface WHY.
                conn.last_status = "error"
                conn.last_error = str(e)[:500]
                logger.warning("Connection %r (%s) unavailable: %s", conn.label, conn.provider, e)

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

        Connection sources (conn:*) come from the latest snapshot — re-fetching
        every request would hit provider rate limits. Manual accounts are cheap
        DB reads, so we take them LIVE: a balance you edit shows up immediately,
        without waiting for the next daily snapshot.

        Net worth partitions into three mutually-exclusive buckets:
          - long_term: sources flagged is_long_term (locked: pension, LISA, ...)
          - committed: the earmarked SLICE of any source tied to a ring-fenced goal
            (liquid but reserved — e.g. a proof-of-funds floor). Only the slice is
            carved out; the rest of a partially-earmarked source stays spendable.
          - spendable: everything else = net_worth - long_term - committed
        Long-term wins over committed: a locked source is never counted committed.
        """
        snapshot = await self.get_latest(user_id)
        # Keep only connection entries from the snapshot; drop its point-in-time
        # account:* rows so the live ones below replace them.
        breakdown: dict[str, float] = {}
        snapshot_date = None
        if snapshot is not None and snapshot.breakdown:
            breakdown = {
                k: v for k, v in snapshot.breakdown.items() if not k.startswith("account:")
            }
            snapshot_date = snapshot.snapshot_date.isoformat()

        long_term_keys: list[str] = []

        # Connections marked long-term feed the spendable/long-term split. Their
        # values live in the snapshot above, keyed conn:{label}.
        connections = await self.db.scalars(
            select(Connection).where(
                Connection.user_id == user_id, Connection.is_active.is_(True)
            )
        )
        for conn in connections:
            if conn.is_long_term:
                long_term_keys.append(f"conn:{conn.label}")

        accounts = await self.db.scalars(
            select(Account).where(Account.user_id == user_id, Account.is_active.is_(True))
        )
        for acct in accounts:
            key = f"account:{acct.name}"
            breakdown[key] = breakdown.get(key, 0.0) + float(acct.balance)
            if acct.is_long_term:
                long_term_keys.append(key)

        # Third bucket: slices earmarked by ring-fenced goals.
        goals = await self.db.scalars(
            select(Goal)
            .where(Goal.user_id == user_id, Goal.ring_fenced.is_(True))
            .options(selectinload(Goal.allocations))
        )
        committed_by_key = _committed_slices(list(goals), breakdown, long_term_keys)
        committed = sum(committed_by_key.values())
        net_worth = sum(breakdown.values())
        long_term = sum(v for k, v in breakdown.items() if k in long_term_keys)
        spendable = net_worth - long_term - committed

        return {
            "date": snapshot_date,
            "net_worth": net_worth,
            "spendable": spendable,
            "long_term": long_term,
            "long_term_keys": long_term_keys,
            "committed": committed,
            "committed_keys": list(committed_by_key.keys()),
            "committed_by_key": committed_by_key,
            "breakdown": breakdown,
        }
