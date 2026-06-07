from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID

from database import get_db
from services.auth import get_current_user
from models.user import User
from services.transaction_service import TransactionService
from schemas.transaction import TransactionCreate, TransactionResponse, TransactionUpdate
from models.transaction import Transaction

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

def get_service(db: AsyncSession = Depends(get_db)):
    return TransactionService(db)

@router.get("/", response_model=list[TransactionResponse])
async def list_transaction(month: int | None = None, year: int | None = None, account_id: int | None = None, user: User = Depends(get_current_user), service: TransactionService = Depends(get_service)):
    return await service.list_transaction(user.id, month, year, account_id)

@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create(body: TransactionCreate, user: User = Depends(get_current_user), service: TransactionService = Depends(get_service)): 
    return await service.create(user.id, body)

@router.patch("/{tx_id}/category", response_model=TransactionResponse)
async def update_category(tx_id: int, body: TransactionUpdate, user: User = Depends(get_current_user), service: TransactionService = Depends(get_service)): 
    return await service.update_category(tx_id, user.id, body.category_id)

@router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(tx_id: int, user: User = Depends(get_current_user), service: TransactionService = Depends(get_service)):
    await service.delete(tx_id, user.id)