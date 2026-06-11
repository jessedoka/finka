from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

class AccountBase(BaseModel):
    name: str
    account_type: str
    currency: str
    institution: str | None
    balance: Decimal
    is_active: bool


class AccountCreate(AccountBase):
    pass

class AccountUpdate(BaseModel):
    pass

class AccountResponse(AccountBase):
    id: int