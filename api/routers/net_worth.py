from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from services.auth import get_current_user
from services.net_worth_service import NetWorthService

router = APIRouter(prefix="/api/net-worth", tags=['net-worth'])


def get_service(db: AsyncSession = Depends(get_db)) -> NetWorthService:
    return NetWorthService(db)


@router.get("/")
async def list_net_worth(
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[NetWorthService, Depends(get_service)],
):
    """The net-worth history series — the fluctuation chart's data source."""
    snapshots = await service.get_series(user.id)
    return [
        {
            "date": s.snapshot_date.isoformat(),
            "net_worth": float(s.net_worth) if s.net_worth is not None else None,
            "total_assets": float(s.total_assets) if s.total_assets is not None else None,
        }
        for s in snapshots
    ]


@router.get("/breakdown")
async def net_worth_breakdown(
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[NetWorthService, Depends(get_service)],
):
    """Per-source split from the latest snapshot (cheap: no live API calls)."""
    snapshot = await service.get_latest(user.id)
    if snapshot is None:
        return {"date": None, "net_worth": None, "breakdown": {}}
    return {
        "date": snapshot.snapshot_date.isoformat(),
        "net_worth": float(snapshot.net_worth) if snapshot.net_worth is not None else None,
        "breakdown": snapshot.breakdown or {},
    }
