"""add goals and goal allocations

Revision ID: 7e8f6a2b5c63
Revises: 6d7e5f1a4b52
Create Date: 2026-07-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7e8f6a2b5c63"
down_revision: Union[str, None] = "6d7e5f1a4b52"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "goals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("target_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("ring_fenced", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_goals_user_id", "goals", ["user_id"])

    op.create_table(
        "goal_allocations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("goal_id", sa.Integer(), nullable=False),
        sa.Column("source_key", sa.String(length=150), nullable=False),
        sa.Column("allocated_amount", sa.Numeric(14, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_goal_allocations_goal_id", "goal_allocations", ["goal_id"])


def downgrade() -> None:
    op.drop_index("ix_goal_allocations_goal_id", table_name="goal_allocations")
    op.drop_table("goal_allocations")
    op.drop_index("ix_goals_user_id", table_name="goals")
    op.drop_table("goals")
