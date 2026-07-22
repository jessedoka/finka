import csv
import io
import json
import zipfile
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from integrations import registry
from integrations.registry import ProviderError
from models.account import Account
from models.connection import Connection
from models.net_worth_snapshot import NetWorthSnapshot
from models.user import User
from services.connection_service import redact_config

# Bump when the export shape changes so consumers/importers can adapt.
# v2: dropped transactions/categories; added connections.
EXPORT_VERSION = 2


def _num(value: Decimal | None) -> str | None:
    """Serialise monetary/decimal values as strings to preserve precision."""
    return str(value) if value is not None else None


def _dt(value: date | datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


ACCOUNT_CSV_FIELDS = [
    "id", "name", "account_type", "currency", "institution", "balance",
    "is_active", "is_long_term", "monthly_contribution", "annual_charge",
    "growth_rate", "created_at", "updated_at",
]

CONNECTION_CSV_FIELDS = [
    "id", "provider", "label", "config", "is_active", "is_long_term",
    "last_synced_at", "last_status", "last_value", "created_at", "updated_at",
]


def _rows_to_csv(rows: list[dict[str, Any]], fields: list[str], json_fields: set[str] = frozenset()) -> str:
    """Serialise a list of flat dicts to CSV text. `json_fields` are dumped as
    a JSON string in their cell rather than spread across columns (e.g. a
    connection's provider-specific `config`)."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        out = dict(row)
        for f in json_fields:
            out[f] = json.dumps(out.get(f))
        writer.writerow(out)
    return buf.getvalue()


def _snapshots_to_csv(snapshots: list[dict[str, Any]]) -> str:
    """Net-worth snapshots, with `breakdown` pivoted into one column per
    source (rather than a nested JSON blob) so the sheet is readable."""
    breakdown_keys: list[str] = []
    seen: set[str] = set()
    for s in snapshots:
        for k in s["breakdown"] or {}:
            # "_"-prefixed keys are snapshot metadata (e.g. `_meta` on
            # backfilled/reconstructed rows), not a source amount — skip them
            # rather than pivoting non-numeric data into a money column.
            if k.startswith("_") or k in seen:
                continue
            seen.add(k)
            breakdown_keys.append(k)

    fields = ["id", "snapshot_date", "total_assets", "total_liabilities", "net_worth", *breakdown_keys]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for s in snapshots:
        row = {k: s[k] for k in ("id", "snapshot_date", "total_assets", "total_liabilities", "net_worth")}
        breakdown = s["breakdown"] or {}
        for k in breakdown_keys:
            row[k] = breakdown.get(k, "")
        writer.writerow(row)
    return buf.getvalue()


class ExportService:
    """Assembles a complete, portable snapshot of one user's data."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def export_user(self, user: User) -> dict[str, Any]:
        accounts = await self._accounts(user.id)
        connections = await self._connections(user.id)
        snapshots = await self._snapshots(user.id)

        return {
            "meta": {
                "export_version": EXPORT_VERSION,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "source": "finka",
                "counts": {
                    "accounts": len(accounts),
                    "connections": len(connections),
                    "net_worth_snapshots": len(snapshots),
                },
            },
            "user": {
                "id": str(user.id),
                "email": user.email,
                "display_name": user.display_name,
                "created_at": _dt(user.created_at),
            },
            "accounts": accounts,
            "connections": connections,
            "net_worth_snapshots": snapshots,
        }

    async def export_csv(self, user: User) -> bytes:
        """Same data as `export_user`, as a zip of one CSV per entity — for
        opening in a spreadsheet rather than re-importing programmatically."""
        accounts = await self._accounts(user.id)
        connections = await self._connections(user.id)
        snapshots = await self._snapshots(user.id)

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("accounts.csv", _rows_to_csv(accounts, ACCOUNT_CSV_FIELDS))
            zf.writestr(
                "connections.csv",
                _rows_to_csv(connections, CONNECTION_CSV_FIELDS, json_fields={"config"}),
            )
            zf.writestr("net_worth_snapshots.csv", _snapshots_to_csv(snapshots))
        return buffer.getvalue()

    async def _accounts(self, user_id: UUID) -> list[dict[str, Any]]:
        rows = await self.db.scalars(
            select(Account).where(Account.user_id == user_id).order_by(Account.id)
        )
        return [
            {
                "id": a.id,
                "name": a.name,
                "account_type": a.account_type,
                "currency": a.currency,
                "institution": a.institution,
                "balance": _num(a.balance),
                "is_active": a.is_active,
                "is_long_term": a.is_long_term,
                "monthly_contribution": _num(a.monthly_contribution),
                "annual_charge": _num(a.annual_charge),
                "growth_rate": _num(a.growth_rate),
                "created_at": _dt(a.created_at),
                "updated_at": _dt(a.updated_at),
            }
            for a in rows
        ]

    async def _connections(self, user_id: UUID) -> list[dict[str, Any]]:
        """Connected sources. Credentials are REDACTED — an export is a file the
        user downloads and shares around; it must never carry live secrets."""
        rows = await self.db.scalars(
            select(Connection).where(Connection.user_id == user_id).order_by(Connection.id)
        )
        out: list[dict[str, Any]] = []
        for c in rows:
            try:
                config = redact_config(registry.get(c.provider), c.config or {})
            except ProviderError:
                # Provider no longer in the registry — omit config rather than
                # risk leaking an unredacted secret.
                config = {}
            out.append(
                {
                    "id": c.id,
                    "provider": c.provider,
                    "label": c.label,
                    "config": config,
                    "is_active": c.is_active,
                    "is_long_term": c.is_long_term,
                    "last_synced_at": _dt(c.last_synced_at),
                    "last_status": c.last_status,
                    "last_value": _num(c.last_value),
                    "created_at": _dt(c.created_at),
                    "updated_at": _dt(c.updated_at),
                }
            )
        return out

    async def _snapshots(self, user_id: UUID) -> list[dict[str, Any]]:
        rows = await self.db.scalars(
            select(NetWorthSnapshot)
            .where(NetWorthSnapshot.user_id == user_id)
            .order_by(NetWorthSnapshot.snapshot_date)
        )
        return [
            {
                "id": s.id,
                "snapshot_date": _dt(s.snapshot_date),
                "total_assets": _num(s.total_assets),
                "total_liabilities": _num(s.total_liabilities),
                "net_worth": _num(s.net_worth),
                "breakdown": s.breakdown,
            }
            for s in rows
        ]
