from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services.auth import get_current_user
from models.user import User
from services.account_service import AccountService
from schemas.account import AccountCreate, AccountResponse, AccountUpdate

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


def get_service(db: AsyncSession = Depends(get_db)):
    return AccountService(db)


@router.get("/", response_model=list[AccountResponse])
async def list_accounts(
    user: User = Depends(get_current_user),
    service: AccountService = Depends(get_service),
):
    return await service.list_accounts(user.id)


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    body: AccountCreate,
    user: User = Depends(get_current_user),
    service: AccountService = Depends(get_service),
):
    return await service.create(user.id, body)


@router.patch("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: int,
    body: AccountUpdate,
    user: User = Depends(get_current_user),
    service: AccountService = Depends(get_service),
):
    return await service.update(account_id, user.id, body)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    user: User = Depends(get_current_user),
    service: AccountService = Depends(get_service),
):
    await service.delete(account_id, user.id)
