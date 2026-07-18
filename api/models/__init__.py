from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Import all models here so Alembic can find them
from .user import User
from .account import Account
from .category import Category
from .transaction import Transaction
from .net_worth_snapshot import NetWorthSnapshot

