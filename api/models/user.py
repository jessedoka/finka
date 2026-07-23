import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import Base

if TYPE_CHECKING:
    from .account import Account
    from .net_worth_snapshot import NetWorthSnapshot
    from .connection import Connection
    from .goal import Goal

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    cognito_sub: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    accounts: Mapped[list["Account"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    net_worth_snapshots: Mapped[list["NetWorthSnapshot"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    connections: Mapped[list["Connection"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    goals: Mapped[list["Goal"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )