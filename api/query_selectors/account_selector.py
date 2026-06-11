from uuid import UUID
from datetime import date
from models.account import Account
from sqlalchemy import select

class AccountSelector: 
    def __init__(self, user_id: UUID):
        self.records = select(Account).where(Account.user_id == user_id).limit(1)