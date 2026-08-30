from database import get_db
from fastapi import HTTPException, Depends, status
from query_selectors.user_selector import UserSelector
from sqlalchemy.ext.asyncio import AsyncSession

class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_user(self, cognito_sub: str):
        user = UserSelector(cognito_sub)
        result = await self.db.scalar(user.records)
        return result
    
async def get_current_user(db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    user = await user_service.get_user('dev-user-001')
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not find user",
        )
    return user
    
    
