from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models.transaction import Transaction

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

@router.get("/count")
async def transaction_count(db: AsyncSession = Depends(get_db)):
    count = await db.scalar(select(func.count()).select_from(Transaction))
    return {"count": count}