"""
TransactionService - creates transaction records and retrieves history.
Kept separate from account_service so transaction-record concerns
(ID uniqueness, ordering, formatting) live in one place.
"""

from __future__ import annotations

from database.db import db
from models.transaction import (
    Transaction,
    DepositTransaction,
    WithdrawalTransaction,
    TransferTransaction,
)


class TransactionService:
    @staticmethod
    def _unique_transaction_id() -> str:
        for _ in range(20):
            candidate = Transaction.generate_transaction_id()
            if Transaction.query.filter_by(transaction_id=candidate).first() is None:
                return candidate
        raise RuntimeError("Could not generate a unique transaction ID.")

    @classmethod
    def record_deposit(cls, account, amount: float, balance_after: float) -> DepositTransaction:
        txn = DepositTransaction(
            transaction_id=cls._unique_transaction_id(),
            account_id=account.id,
            amount=amount,
            fee=0.0,
            status="SUCCESS",
            balance_after=balance_after,
            note="Cash deposit",
        )
        db.session.add(txn)
        return txn

    @classmethod
    def record_withdrawal(
        cls, account, amount: float, fee: float, balance_after: float
    ) -> WithdrawalTransaction:
        txn = WithdrawalTransaction(
            transaction_id=cls._unique_transaction_id(),
            account_id=account.id,
            amount=amount,
            fee=fee,
            status="SUCCESS",
            balance_after=balance_after,
            note="ATM cash withdrawal",
        )
        db.session.add(txn)
        return txn

    @classmethod
    def record_transfer(
        cls, account, amount: float, fee: float, balance_after: float, related_account_number: str, note: str
    ) -> TransferTransaction:
        txn = TransferTransaction(
            transaction_id=cls._unique_transaction_id(),
            account_id=account.id,
            amount=amount,
            fee=fee,
            status="SUCCESS",
            balance_after=balance_after,
            related_account_number=related_account_number,
            note=note,
        )
        db.session.add(txn)
        return txn

    @staticmethod
    def get_mini_statement(account, limit: int = 5) -> list[Transaction]:
        return (
            Transaction.query.filter_by(account_id=account.id)
            .order_by(Transaction.timestamp.desc())
            .limit(limit)
            .all()
        )
