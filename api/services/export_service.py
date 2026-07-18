from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.account import Account
from models.category import Category
from models.net_worth_snapshot import NetWorthSnapshot
from models.transaction import Transaction
from models.user import User

# Bump when the export shape changes so consumers/importers can adapt.
EXPORT_VERSION = 1


def _num(value: Decimal | None) -> str | None:
    """Serialise monetary/decimal values as strings to preserve precision."""
    return str(value) if value is not None else None


def _dt(value: date | datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


class ExportService:
    """Assembles a complete, portable snapshot of one user's data."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def export_user(self, user: User) -> dict[str, Any]:
        accounts = await self._accounts(user.id)
        categories = await self._categories(user.id)
        transactions = await self._transactions(user.id)
        snapshots = await self._snapshots(user.id)

        return {
            "meta": {
                "export_version": EXPORT_VERSION,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "source": "finka",
                "counts": {
                    "accounts": len(accounts),
                    "categories": len(categories),
                    "transactions": len(transactions),
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
            "categories": categories,
            "transactions": transactions,
            "net_worth_snapshots": snapshots,
        }

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

    async def _categories(self, user_id: UUID) -> list[dict[str, Any]]:
        rows = await self.db.scalars(
            select(Category).where(Category.user_id == user_id).order_by(Category.id)
        )
        return [
            {
                "id": c.id,
                "name": c.name,
                "colour": c.colour,
                "icon": c.icon,
                "is_income": c.is_income,
            }
            for c in rows
        ]

    async def _transactions(self, user_id: UUID) -> list[dict[str, Any]]:
        rows = await self.db.scalars(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.transaction_date, Transaction.id)
        )
        return [
            {
                "id": t.id,
                "account_id": t.account_id,
                "category_id": t.category_id,
                "amount": _num(t.amount),
                "description": t.description,
                "merchant_name": t.merchant_name,
                "transaction_date": _dt(t.transaction_date),
                "external_id": t.external_id,
                "created_at": _dt(t.created_at),
            }
            for t in rows
        ]

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
