from uuid import UUID
from query_selectors.account_selector import AccountSelector
from sqlalchemy.ext.asyncio import AsyncSession 
from schemas.account import AccountCreate
from models.account import Account

class AccountService: 
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_accounts(self, user_id: UUID, month: int | None, year: int | None, account_id: int | None): 
        accounts = AccountSelector(user_id)
        result = await self.db.execute(accounts.records)
        return result.scalars().all()
    
    async def create(self, user_id: UUID, data: AccountCreate): 
        tx = Account(user_id=user_id, **data.model_dump())
        self.db.add(tx)

        await self.db.commit()
        await self.db.refresh(tx) 
        return tx 

    async def update_field(self, account_id: int, user_id: UUID, category_id: int | None):
        # this can be any field. 
        account = await self._get_owned(account_id, user_id)
        # account.category_id = category_id

        await self.db.commit()
        await self.db.refresh(account)
        return account

    async def delete(self, account_id: int, user_id: UUID):
        tx = await self._get_owned(account_id, user_id)

        await self.db.delete(tx)
        await self.db.commit()

    async def _get_owned(self, account_id: int, user_id: UUID):
        account = AccountSelector(user_id) # grab specific 
        tx = await self.db.scalar(account.records)
        if tx is None: 
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Transaction not found")
        return tx

