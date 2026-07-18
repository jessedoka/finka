from uuid import UUID
from models.account import Account
from sqlalchemy import select


class AccountSelector:
    def __init__(self, user_id: UUID):
        self.user_id = user_id
        # All accounts for the user, newest first.
        self.records = (
            select(Account)
            .where(Account.user_id == user_id)
            .order_by(Account.created_at.desc())
        )

    def select_by_account(self, account_id: int):
        """A single owned account, or nothing if it isn't theirs."""
        return select(Account).where(
            Account.id == account_id,
            Account.user_id == self.user_id,
        )
