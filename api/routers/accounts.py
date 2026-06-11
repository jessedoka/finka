from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID

from database import get_db
from services.auth import get_current_user
from models.user import User
from services.account_service import AccountService
from schemas.transaction import TransactionCreate, TransactionResponse, TransactionUpdate

router = APIRouter(prefix="/api/accounts", tags=['accounts'])

def get_service(db: AsyncSession = Depends(get_db)):
    return AccountService(db)

@router.get("/")
async def list_accounts():
    return {"message": "not implemented yet"}

