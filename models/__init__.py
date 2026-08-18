"""
Importing this package registers every SQLAlchemy model with the shared
`db` metadata, so `db.create_all()` in app.py picks up all tables.
"""

from models.customer import Customer
from models.card import Card
from models.account import Account, SavingsAccount, CurrentAccount, DailyLimitTracker
from models.transaction import (
    Transaction,
    DepositTransaction,
    WithdrawalTransaction,
    TransferTransaction,
)
from models.atm import CashDenomination, ATM
from models.bank import Bank

__all__ = [
    "Customer",
    "Card",
    "Account",
    "SavingsAccount",
    "CurrentAccount",
    "DailyLimitTracker",
    "Transaction",
    "DepositTransaction",
    "WithdrawalTransaction",
    "TransferTransaction",
    "CashDenomination",
    "ATM",
    "Bank",
]
