from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID

from database import get_db
from services.transaction_service import TransactionService
from schemas.transaction import TransactionCreate, TransactionResponse, TransactionUpdate
from models.transaction import Transaction

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

def get_service(db: AsyncSession = Depends(get_db)):
    return TransactionService(db)

def current_user_id():
    return UUID("00000000-0000-0000-0000-000000000001")

@router.get("/", response_model=list[TransactionResponse])
async def list_transaction(month: int | None, year: int | None, account_id: int | None, service: TransactionService = Depends(get_service)):
    user_id = current_user_id()
    return await service.list_transaction(user_id, month, year, account_id)

@router.get("/count")
async def transaction_count(db: AsyncSession = Depends(get_db)):
    count = await db.scalar(select(func.count()).select_from(Transaction))
    return {"count": count}

@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create(body: TransactionCreate, service: TransactionService = Depends(get_service)): 
    user_id = current_user_id()
    return await service.create(user_id, body)

@router.patch("/{tx_id}/category", response_model=TransactionResponse)
async def update_category(tx_id: int, body: TransactionUpdate, service: TransactionService = Depends(get_service)): 
    user_id = current_user_id()
    return await service.update_category(tx_id, user_id, body.category_id)

@router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(tx_id: int, service: TransactionService = Depends(get_service)):
    user_id = current_user_id()
    await service.delete(tx_id, user_id)