from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from schemas.goal import (
    AllocationCreate,
    GoalCreate,
    GoalDetail,
    GoalProgress,
    GoalUpdate,
)
from services.auth import get_current_user
from services.goal_service import GoalService

router = APIRouter(prefix="/api/goals", tags=["goals"])


def get_service(db: AsyncSession = Depends(get_db)) -> GoalService:
    return GoalService(db)


async def _detail_or_404(service: GoalService, user_id, goal_id: int) -> dict:
    detail = await service.detail(user_id, goal_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    return detail


@router.get("/", response_model=list[GoalProgress])
async def list_goals(
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[GoalService, Depends(get_service)],
):
    """Every goal with funded/remaining/run-rate — one breakdown read for all, no series."""
    return await service.list_with_progress(user.id)


@router.get("/{goal_id}", response_model=GoalDetail)
async def get_goal(
    goal_id: int,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[GoalService, Depends(get_service)],
):
    """One goal's progress plus its funding-over-time series and inferred run-rate."""
    return await _detail_or_404(service, user.id, goal_id)


@router.post("/", response_model=GoalDetail, status_code=status.HTTP_201_CREATED)
async def create_goal(
    body: GoalCreate,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[GoalService, Depends(get_service)],
):
    goal = await service.create(user.id, body)
    return await _detail_or_404(service, user.id, goal.id)


@router.patch("/{goal_id}", response_model=GoalDetail)
async def update_goal(
    goal_id: int,
    body: GoalUpdate,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[GoalService, Depends(get_service)],
):
    await service.update(user.id, goal_id, body)
    return await _detail_or_404(service, user.id, goal_id)


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: int,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[GoalService, Depends(get_service)],
):
    await service.delete(user.id, goal_id)


@router.post("/{goal_id}/allocations", response_model=GoalDetail, status_code=status.HTTP_201_CREATED)
async def add_allocation(
    goal_id: int,
    body: AllocationCreate,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[GoalService, Depends(get_service)],
):
    """Earmark a source (account:{name} / conn:{label}) toward the goal."""
    await service.add_allocation(user.id, goal_id, body)
    return await _detail_or_404(service, user.id, goal_id)


@router.delete("/{goal_id}/allocations/{allocation_id}", response_model=GoalDetail)
async def remove_allocation(
    goal_id: int,
    allocation_id: int,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[GoalService, Depends(get_service)],
):
    await service.remove_allocation(user.id, goal_id, allocation_id)
    return await _detail_or_404(service, user.id, goal_id)
