"""drop transactions and categories

Finka is a net-worth tracker: balances per source over time. The spending-tracker
half (transactions + categories) was never wired into the UI and is removed.

Revision ID: 6d7e5f1a4b52
Revises: 5c6d4e0f3a41
Create Date: 2026-07-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6d7e5f1a4b52"
down_revision: Union[str, None] = "5c6d4e0f3a41"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # transactions FKs categories, so it goes first. Dropping a table drops its
    # indexes with it.
    op.drop_table("transactions")
    op.drop_table("categories")


def downgrade() -> None:
    """Recreates the table structure exactly as 181c1a9a209e defined it.

    Row data is NOT recoverable — this is a structural rollback only.
    """
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("colour", sa.String(length=7), nullable=True),
        sa.Column("icon", sa.String(length=50), nullable=True),
        sa.Column("is_income", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name", name="uq_category_user_name"),
    )
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("merchant_name", sa.String(length=200), nullable=True),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("account_id", "external_id", name="uq_transaction_external"),
    )
    op.create_index("idx_transactions_account", "transactions", ["account_id", "transaction_date"])
    op.create_index("idx_transactions_user_category", "transactions", ["user_id", "category_id"])
    op.create_index("idx_transactions_user_date", "transactions", ["user_id", "transaction_date"])
