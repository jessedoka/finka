from typing import Annotated

from jwt import decode, PyJWKClient
from database import get_db
from fastapi import HTTPException, Depends, status
from query_selectors.user_selector import UserSelector
from sqlalchemy.ext.asyncio import AsyncSession 
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from config import settings

URI = f"https://cognito-idp.{settings.aws_region}.amazonaws.com/{settings.cognito_user_pool_id}/.well-known/jwks.json"
ISS = f"https://cognito-idp.{settings.aws_region}.amazonaws.com/{settings.cognito_user_pool_id}"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=(settings.environment != 'development'))
jwt_client = PyJWKClient(URI)
ALGORITHM = "RS256"

class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_user(self, cognito_sub: str):
        user = UserSelector(cognito_sub)
        result = await self.db.scalar(user.records)
        return result
    
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    missing_user_exception = HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Could not find user",
    )

    if settings.environment == 'development':
            dev_user = await user_service.get_user("dev-user-001")

            if dev_user is None:
                raise missing_user_exception 
            return dev_user 
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        signed_key = jwt_client.get_signing_key_from_jwt(token)
        payload = decode(token, signed_key.key, algorithms=[ALGORITHM])
       
        if payload.get('iss') != ISS or payload.get('client_id') != settings.cognito_app_client_id or payload.get('token_use') != "access":
            raise credentials_exception
        
        sub = payload.get("sub")

        if sub is None:
            raise credentials_exception
        
        user = await user_service.get_user(sub)
        if user is None:
            raise credentials_exception
        return user

    except InvalidTokenError:
        raise credentials_exception
    
    
