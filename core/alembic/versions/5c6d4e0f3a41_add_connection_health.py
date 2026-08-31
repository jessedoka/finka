"""add connection sync health columns

Revision ID: 5c6d4e0f3a41
Revises: 4b5c3d9e2f30
Create Date: 2026-07-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5c6d4e0f3a41"
down_revision: Union[str, None] = "4b5c3d9e2f30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("connections", sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("connections", sa.Column("last_status", sa.String(length=10), nullable=True))
    op.add_column("connections", sa.Column("last_error", sa.String(length=500), nullable=True))
    op.add_column("connections", sa.Column("last_value", sa.Numeric(14, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("connections", "last_value")
    op.drop_column("connections", "last_error")
    op.drop_column("connections", "last_status")
    op.drop_column("connections", "last_synced_at")
