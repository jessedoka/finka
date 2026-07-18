from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class AccountBase(BaseModel):
    name: str
    account_type: str
    currency: str = "GBP"
    institution: str | None = None
    balance: Decimal = Decimal("0.00")
    is_active: bool = True


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    """All optional — PATCH only touches the fields that are provided."""
    name: str | None = None
    account_type: str | None = None
    currency: str | None = None
    institution: str | None = None
    balance: Decimal | None = None
    is_active: bool | None = None


class AccountResponse(AccountBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
