from models.user import User
from sqlalchemy import select

class UserSelector: 
    def __init__(self, cognito_sub: str):
        self.records = select(User).where(User.cognito_sub == cognito_sub).limit(1)