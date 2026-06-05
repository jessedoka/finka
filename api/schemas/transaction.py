from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

class TransactionBase(BaseModel):
    account_id: int
    amount: Decimal
    description: str
    merchant_name: str | None = None
    transaction_date: date
    category_id: int | None = None

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    category_id: int | None = None
    description: str | None = None

class TransactionResponse(TransactionBase):
    id: int
    category_name: str | None = None
    model_config = ConfigDict(from_attributes=True)