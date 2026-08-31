import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import Integer, Date, Numeric, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import Base

if TYPE_CHECKING:
    from .user import User

class NetWorthSnapshot(Base):
    __tablename__ = "net_worth_snapshots"
    __table_args__ = (
        UniqueConstraint("user_id", "snapshot_date", name="uq_networth_user_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_assets: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    total_liabilities: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    net_worth: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    breakdown: Mapped[dict | None] = mapped_column(JSON)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="net_worth_snapshots")