"""Read-only Trading212 passthrough (MECHANICAL / plumbing only).

Exposes your LIVE T212 numbers to the frontend so the "current amount" half of
the dashboard renders the instant a real key is in api/.env. It does NOT touch
the database and does NOT map onto Account/NetWorthSnapshot — that persistence
+ history logic is services/trading212_service.py, which is yours to write.

SECURITY / PROD: this endpoint is intentionally UNAUTHENTICATED for Phase 0
local dev (auth is stubbed). It returns your personal financial data, so it
MUST be put behind get_current_user (like the other routers) before this is
ever deployed. Do not ship it open.
"""

from decimal import Decimal

from fastapi import APIRouter, HTTPException

from integrations.trading212 import Trading212Client, Trading212Error

router = APIRouter(prefix="/api/integrations/trading212", tags=["trading212"])


@router.get("/summary")
async def summary():
    """Live snapshot: cash blob + open positions, straight from T212.

    Returns T212's fields verbatim plus a convenience `positions_value` (sum of
    quantity * currentPrice) so the frontend has one portfolio number to show.
    Deciding which figure is THE headline "current amount" is your call in the
    service layer — this just surfaces the raw material.
    """
    client = Trading212Client()
    if client.api_key in ("", "local", None):
        raise HTTPException(
            status_code=503,
            detail="Trading212 key not configured. Set trading_212_key in api/.env.",
        )

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
