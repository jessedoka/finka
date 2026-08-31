"""add account is_long_term

Revision ID: 3a4b2c8d1e20
Revises: 2f3a1b7c9d10
Create Date: 2026-07-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3a4b2c8d1e20"
down_revision: Union[str, None] = "2f3a1b7c9d10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "accounts",
        sa.Column(
            "is_long_term",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )


def downgrade() -> None:
    op.drop_column("accounts", "is_long_term")
