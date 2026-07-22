"""Read-only Trading212 passthrough (MECHANICAL / plumbing only).

Exposes the user's LIVE T212 numbers to the frontend so the "current amount"
half of the dashboard renders as soon as they've added a Trading212 connection.
It does NOT touch the net-worth tables — that persistence + history logic lives
in the net-worth service. This is just the detailed portfolio view.

The T212 key comes from the user's active `trading212` Connection (added via the
Connections page), NOT a global env var — so it works for any user, not just the
instance owner.
"""

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from integrations.trading212 import DEMO_BASE_URL, LIVE_BASE_URL, Trading212Client, Trading212Error
from models.connection import Connection
from models.user import User
from services.auth import get_current_user

router = APIRouter(prefix="/api/integrations/trading212", tags=["trading212"])


async def _client_for(user: User, db: AsyncSession) -> Trading212Client:
    """Build a client from the user's active Trading212 connection, or 503."""
    conn = await db.scalar(
        select(Connection)
        .where(
            Connection.user_id == user.id,
            Connection.provider == "trading212",
            Connection.is_active.is_(True),
        )
        .order_by(Connection.created_at)
    )
    config = (conn.config if conn else None) or {}
    api_key = config.get("api_key")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="No Trading212 connection. Add one on the Connections page.",
        )
    base_url = DEMO_BASE_URL if config.get("demo") else LIVE_BASE_URL
    return Trading212Client(api_key=api_key, base_url=base_url)


@router.get("/summary")
async def summary(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Live snapshot: cash blob + open positions, straight from T212.

    Returns T212's fields verbatim plus a convenience `positions_value` (sum of
    quantity * currentPrice) so the frontend has one portfolio number to show.
    """
    client = await _client_for(user, db)

    try:
        cash = await client.fetch_cash()
        portfolio = await client.fetch_portfolio()
    except Trading212Error as e:
        raise HTTPException(status_code=502, detail=str(e))

    positions_value = sum(
        Decimal(str(p.get("quantity", 0))) * Decimal(str(p.get("currentPrice", 0)))
        for p in portfolio
    )

    return {
        "cash": cash,
        "positions": portfolio,
        "positions_value": float(positions_value),
    }
