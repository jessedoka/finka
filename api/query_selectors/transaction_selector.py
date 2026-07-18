from uuid import UUID
from datetime import date
from models.transaction import Transaction
from sqlalchemy import select

class TransactionSelector: 
    def __init__(self, user_id: UUID):
        self.records = select(Transaction).where(Transaction.user_id == user_id).order_by(Transaction.transaction_date.desc())

    def select_within_a_year(self, month: int, year: int):
        self.records = self.records.where(
            Transaction.transaction_date >= date(year, month, 1),
            Transaction.transaction_date < date(year + (month // 12), (month % 12) + 1, 1)
        )
        return self

    def select_by_account(self, account_id: int):
        self.records = self.records.where(Transaction.account_id == account_id)
        return self

    def select_by_transaction(self, tx_id: int):
        self.records = self.records.where(Transaction.id == tx_id)
        return self