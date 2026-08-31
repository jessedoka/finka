from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Import all models here so Alembic can find them
from .user import User
from .account import Account
from .net_worth_snapshot import NetWorthSnapshot
from .connection import Connection
from .goal import Goal, GoalAllocation

