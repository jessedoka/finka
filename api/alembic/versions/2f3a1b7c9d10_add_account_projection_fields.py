"""add account projection fields

Revision ID: 2f3a1b7c9d10
Revises: 181c1a9a209e
Create Date: 2026-07-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2f3a1b7c9d10"
down_revision: Union[str, None] = "181c1a9a209e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "accounts",
        sa.Column(
            "monthly_contribution",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "accounts",
        sa.Column(
            "annual_charge",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "accounts",
        sa.Column(
            "growth_rate",
            sa.Numeric(precision=6, scale=4),
            nullable=False,
            server_default="0.05",
        ),
    )


def downgrade() -> None:
    op.drop_column("accounts", "growth_rate")
    op.drop_column("accounts", "annual_charge")
    op.drop_column("accounts", "monthly_contribution")
