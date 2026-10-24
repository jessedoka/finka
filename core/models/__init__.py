from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Import all models here so Alembic can find them. They import Base from this
# module, so they can only be imported after it is defined (hence E402), and
# they are imported for their side effect of registering tables (hence F401).
# ruff: noqa: E402, F401
from .user import User
from .account import Account
from .net_worth_snapshot import NetWorthSnapshot
from .connection import Connection
from .goal import Goal, GoalAllocation

