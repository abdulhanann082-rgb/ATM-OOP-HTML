"""
Transaction hierarchy: Transaction (base) -> DepositTransaction /
WithdrawalTransaction / TransferTransaction.

Demonstrates inheritance + polymorphism: each subclass implements
`display_amount()` and `describe()` differently (deposits show as +amount,
withdrawals/transfers as -amount, etc.) even though callers just treat
every record as a generic Transaction.
"""

from __future__ import annotations

import random
import string
from datetime import datetime

from database.db import db


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(20), unique=True, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # discriminator
    account_id = db.Column(db.Integer, db.ForeignKey("accounts.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    fee = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(20), nullable=False, default="SUCCESS")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    balance_after = db.Column(db.Float, nullable=False)
    note = db.Column(db.String(255))

    # Only relevant for transfers: the other side of the transaction.
    related_account_number = db.Column(db.String(20))

    __mapper_args__ = {
        "polymorphic_identity": "transaction",
        "polymorphic_on": transaction_type,
    }

    @staticmethod
    def generate_transaction_id() -> str:
        return "TXN-" + "".join(random.choices(string.digits, k=6))

    def display_amount(self) -> str:
        """Polymorphic hook - overridden by each subclass."""
        return f"{self.amount:,.2f}"

    def describe(self) -> str:
        return f"{self.transaction_type} of Rs. {self.display_amount()}"

    def __repr__(self) -> str:
        return f"<Transaction {self.transaction_id} {self.transaction_type} {self.amount}>"


class DepositTransaction(Transaction):
    __mapper_args__ = {"polymorphic_identity": "DEPOSIT"}

    def display_amount(self) -> str:
        return f"+{self.amount:,.2f}"


class WithdrawalTransaction(Transaction):
    __mapper_args__ = {"polymorphic_identity": "WITHDRAWAL"}

    def display_amount(self) -> str:
        return f"-{self.amount:,.2f}"


class TransferTransaction(Transaction):
    __mapper_args__ = {"polymorphic_identity": "TRANSFER"}

    def display_amount(self) -> str:
        sign = "-" if self.note and "sent" in self.note.lower() else "+"
        return f"{sign}{self.amount:,.2f}"
