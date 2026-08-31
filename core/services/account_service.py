from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from models.account import Account
from query_selectors.account_selector import AccountSelector
from schemas.account import AccountCreate, AccountUpdate


class AccountService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_accounts(self, user_id: UUID) -> list[Account]:
        result = await self.db.execute(AccountSelector(user_id).records)
        return list(result.scalars().all())

    async def get(self, account_id: int, user_id: UUID) -> Account:
        return await self._get_owned(account_id, user_id)

    async def create(self, user_id: UUID, data: AccountCreate) -> Account:
        account = Account(user_id=user_id, **data.model_dump())
        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)
        return account

    async def update(self, account_id: int, user_id: UUID, data: AccountUpdate) -> Account:
        account = await self._get_owned(account_id, user_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(account, field, value)
        await self.db.commit()
        await self.db.refresh(account)
        return account

    async def delete(self, account_id: int, user_id: UUID) -> None:
        account = await self._get_owned(account_id, user_id)
        await self.db.delete(account)
        await self.db.commit()

    async def _get_owned(self, account_id: int, user_id: UUID) -> Account:
        stmt = AccountSelector(user_id).select_by_account(account_id)
        account = await self.db.scalar(stmt)
        if account is None:
            raise HTTPException(status_code=404, detail="Account not found")
        return account
