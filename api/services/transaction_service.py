from uuid import UUID
from query_selectors.transaction_selector import TransactionSelector
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload 
from schemas.transaction import TransactionCreate
from models.transaction import Transaction

class TransactionService: 
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_transaction(self, user_id: UUID, month: int | None, year: int | None, account_id: int | None): 
        transactions = TransactionSelector(user_id)

        if month and year: 
            transactions = transactions.select_within_a_year(month, year)
        
        if account_id: 
            transactions = transactions.select_by_account(account_id)

        result = await self.db.execute(transactions.records)
        return result.scalars().all()
    
    async def create(self, user_id: UUID, data: TransactionCreate): 
        tx = Transaction(user_id=user_id, **data.model_dump())
        self.db.add(tx)

        await self.db.commit()
        await self.db.refresh(tx) 
        return tx 

    async def update_category(self, tx_id: int, user_id: UUID, category_id: int | None):
        tx = await self._get_owned(tx_id, user_id)
        tx.category_id = category_id

        await self.db.commit()
        await self.db.refresh(tx)
        return tx

    async def delete(self, tx_id: int, user_id: UUID):
        tx = await self._get_owned(tx_id, user_id)

        await self.db.delete(tx)
        await self.db.commit()

    async def _get_owned(self, tx_id: int, user_id: UUID):
        transactions = TransactionSelector(user_id).select_by_transaction(tx_id)
        tx = await self.db.scalar(transactions.records)
        if tx is None: 
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Transaction not found")
        return tx

