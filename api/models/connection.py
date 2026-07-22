import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, Numeric, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import Base

if TYPE_CHECKING:
    from .user import User


class Connection(Base):
    """A user-configured data source ("bring your own source").

    Each row is one instance of a registry provider (monzo / trading212 /
    coinbase / http). `config` holds that provider's credentials plus any
    provider-specific settings (see integrations/registry.py for the field
    schema per provider). Replacing the old hardcoded env-based integrations:
    a source is now data, not code.

    TODO(encrypt): `config` stores secrets in plaintext for the self-host phase.
    Encrypt at rest before multi-tenant hosting.
    """

    __tablename__ = "connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    # Registry key: monzo / trading212 / coinbase / http.
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    # User-facing name; also the breakdown key ("conn:{label}").
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Long-term / locked — excluded from the "spendable" view (mirrors Account).
    is_long_term: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    # Sync health, written on each snapshot. Lets the UI show WHY an active source
    # isn't contributing (e.g. an expired token) instead of silently dropping it.
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_status: Mapped[str | None] = mapped_column(String(10))  # "ok" | "error"
    last_error: Mapped[str | None] = mapped_column(String(500))
    last_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="connections")
