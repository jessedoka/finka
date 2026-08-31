from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from services.auth import get_current_user
from services.net_worth_service import NetWorthService
from services.projection_service import ProjectionService

router = APIRouter(prefix="/api/net-worth", tags=['net-worth'])


def get_service(db: AsyncSession = Depends(get_db)) -> NetWorthService:
    return NetWorthService(db)


def get_projection_service(db: AsyncSession = Depends(get_db)) -> ProjectionService:
    return ProjectionService(db)


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


@router.post("/snapshot", status_code=status.HTTP_201_CREATED)
async def record_snapshot(
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[NetWorthService, Depends(get_service)],
):
    """Re-poll every connected source now and record today's snapshot.

    The daily scheduler does this on a timer; this lets the UI refresh on demand
    (e.g. right after adding or fixing a connection) instead of waiting a day.
    """
    await service.record_snapshot(user.id)
    return await service.get_current_breakdown(user.id)


@router.get("/breakdown")
async def net_worth_breakdown(
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[NetWorthService, Depends(get_service)],
):
    """Live per-source split: snapshot providers + current manual accounts."""
    return await service.get_current_breakdown(user.id)


@router.get("/projection")
async def net_worth_projection(
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ProjectionService, Depends(get_projection_service)],
    years: int = Query(10, ge=1, le=50),
):
    """Projected net worth over `years`, with contributions and compound growth."""
    return await service.project(user.id, years)
