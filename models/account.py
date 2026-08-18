"""
Account hierarchy: Account (base) -> SavingsAccount / CurrentAccount.

Demonstrates:
    - Encapsulation: balance, pin hash and status are stored in "protected"
      attributes and can only be changed through controlled methods.
    - Inheritance: SavingsAccount and CurrentAccount extend Account.
    - Polymorphism: calculate_withdrawal_limit() and get_withdrawal_fee()
      behave differently for each subclass.
    - Abstraction: Account defines the contract; subclasses must implement
      calculate_withdrawal_limit().
"""

from __future__ import annotations

import random
import string
from abc import abstractmethod
from datetime import datetime, date

from werkzeug.security import generate_password_hash, check_password_hash

from database.db import db
from exceptions.custom_exceptions import (
    InvalidPINError,
    InsufficientBalanceError,
    InvalidAmountError,
    AccountInactiveError,
)

WITHDRAWAL_FEE = 50
TRANSFER_FEE = 100
MIN_WITHDRAWAL_AMOUNT = 500
MAX_WITHDRAWAL_PER_TRANSACTION = 50000
DAILY_WITHDRAWAL_LIMIT = 100000


class Account(db.Model):
    """
    Abstract-style base class for all bank accounts.

    Sensitive fields (`_balance`, `_pin_hash`, `_status`) are exposed only
    through read-only properties or controlled methods, so code like
    `account.balance = -50000` is impossible - it raises AttributeError
    because `balance` has no setter.
    """

    __tablename__ = "accounts"

    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(20), unique=True, nullable=False)
    account_type = db.Column(db.String(20), nullable=False)  # discriminator
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)

    # "protected" storage - name-mangled at the DB-column level only.
    _balance = db.Column("balance", db.Float, nullable=False, default=0.0)
    _pin_hash = db.Column("pin_hash", db.String(255), nullable=False)
    _status = db.Column("status", db.String(20), nullable=False, default="ACTIVE")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    transactions = db.relationship(
        "Transaction", backref="account", lazy=True, order_by="desc(Transaction.timestamp)"
    )
    daily_limits = db.relationship("DailyLimitTracker", backref="account", lazy=True)

    __mapper_args__ = {
        "polymorphic_identity": "account",
        "polymorphic_on": account_type,
    }

    # ------------------------------------------------------------------ #
    # Construction helpers
    # ------------------------------------------------------------------ #
    def initialize(self, pin: str, opening_balance: float = 0.0) -> None:
        """Set up a brand-new account (used instead of a public balance/pin setter)."""
        self.account_number = self._generate_account_number()
        self._pin_hash = generate_password_hash(pin)
        self._balance = opening_balance
        self._status = "ACTIVE"

    @staticmethod
    def _generate_account_number() -> str:
        return "".join(random.choices(string.digits, k=10))

    # ------------------------------------------------------------------ #
    # Read-only properties (encapsulation)
    # ------------------------------------------------------------------ #
    @property
    def balance(self) -> float:
        return self._balance

    @property
    def status(self) -> str:
        return self._status

    # ------------------------------------------------------------------ #
    # Authentication / PIN
    # ------------------------------------------------------------------ #
    def verify_pin(self, pin: str) -> bool:
        return check_password_hash(self._pin_hash, pin)

    def change_pin(self, current_pin: str, new_pin: str, confirm_pin: str) -> None:
        """
        Change the account PIN.

        Verifies the current PIN, validates the new PIN, confirms it matches,
        then stores only the hash - the plain PIN is never persisted or logged.
        """
        if not self.verify_pin(current_pin):
            raise InvalidPINError("Current PIN is incorrect.")
        if new_pin != confirm_pin:
            raise InvalidPINError("New PIN and confirmation do not match.")
        self._validate_new_pin(new_pin)
        self._pin_hash = generate_password_hash(new_pin)

    @staticmethod
    def _validate_new_pin(pin: str) -> None:
        if not (pin.isdigit() and len(pin) == 4):
            raise InvalidPINError("PIN must be exactly 4 digits.")

    # ------------------------------------------------------------------ #
    # Status control
    # ------------------------------------------------------------------ #
    def ensure_active(self) -> None:
        if self._status != "ACTIVE":
            raise AccountInactiveError(f"Account is {self._status} and cannot perform transactions.")

    def block(self) -> None:
        self._status = "BLOCKED"

    def activate(self) -> None:
        self._status = "ACTIVE"

    # ------------------------------------------------------------------ #
    # Core money operations (the ONLY way balance may change)
    # ------------------------------------------------------------------ #
    def deposit(self, amount: float) -> None:
        self.ensure_active()
        if amount <= 0:
            raise InvalidAmountError("Deposit amount must be positive.")
        self._balance += amount

    def withdraw(self, amount: float, fee: float = 0.0) -> None:
        """
        Validate the requested cash AMOUNT against this account type's rules,
        then debit (amount + fee) from the balance. The per-transaction and
        minimum limits apply to the cash amount actually dispensed, not the
        service fee riding along with it.
        """
        self.ensure_active()
        if amount < MIN_WITHDRAWAL_AMOUNT:
            raise InvalidAmountError(f"Withdrawal amount must be at least Rs. {MIN_WITHDRAWAL_AMOUNT}.")
        if amount > MAX_WITHDRAWAL_PER_TRANSACTION:
            raise InvalidAmountError(
                f"Withdrawal amount cannot exceed Rs. {MAX_WITHDRAWAL_PER_TRANSACTION} per transaction."
            )
        total_debit = amount + fee
        self._validate_withdrawal(total_debit)
        self._balance -= total_debit

    def credit(self, amount: float) -> None:
        """Internal credit used by transfers (receiver side); still validated."""
        self.ensure_active()
        if amount <= 0:
            raise InvalidAmountError("Amount must be positive.")
        self._balance += amount

    def debit(self, amount: float) -> None:
        """Internal debit used by transfers (sender side); still validated."""
        self.ensure_active()
        if amount <= 0:
            raise InvalidAmountError("Amount must be positive.")
        self._validate_sufficient_funds(amount)
        self._balance -= amount

    def check_balance(self) -> float:
        self.ensure_active()
        return self._balance

    # ------------------------------------------------------------------ #
    # Abstract / polymorphic hooks - subclasses MUST override
    # ------------------------------------------------------------------ #
    @abstractmethod
    def calculate_withdrawal_limit(self) -> float:
        """Return the max amount withdrawable per transaction for this account type."""
        raise NotImplementedError("Subclasses must implement calculate_withdrawal_limit().")

    def _validate_withdrawal(self, amount: float) -> None:
        raise NotImplementedError("Subclasses must implement _validate_withdrawal().")

    def _validate_sufficient_funds(self, amount: float) -> None:
        raise NotImplementedError("Subclasses must implement _validate_sufficient_funds().")

    def get_withdrawal_fee(self) -> float:
        return WITHDRAWAL_FEE

    def get_transfer_fee(self) -> float:
        return TRANSFER_FEE

    # ------------------------------------------------------------------ #
    # Daily limit helpers
    # ------------------------------------------------------------------ #
    def get_or_create_today_tracker(self) -> "DailyLimitTracker":
        today = date.today()
        tracker = next((t for t in self.daily_limits if t.tracked_date == today), None)
        if tracker is None:
            tracker = DailyLimitTracker(
                account_id=self.id,
                tracked_date=today,
                withdrawn_amount=0.0,
                transferred_amount=0.0,
            )
            db.session.add(tracker)
            db.session.flush()
        return tracker

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.account_number} status={self._status}>"


class SavingsAccount(Account):
    """Savings account: minimum balance requirement, conservative withdrawal cap."""

    __mapper_args__ = {"polymorphic_identity": "SAVINGS"}

    MIN_BALANCE = 5000
    MAX_WITHDRAWAL = 50000

    def calculate_withdrawal_limit(self) -> float:
        """Savings accounts may withdraw up to MAX_WITHDRAWAL, bounded by what
        can be left over the minimum balance requirement."""
        available_above_minimum = max(self._balance - self.MIN_BALANCE, 0)
        return min(self.MAX_WITHDRAWAL, available_above_minimum)

    def _validate_withdrawal(self, total_debit: float) -> None:
        """`total_debit` is the cash amount PLUS any fee already added by the caller."""
        if self._balance - total_debit < self.MIN_BALANCE:
            raise InsufficientBalanceError(
                f"Withdrawal would breach the minimum balance of Rs. {self.MIN_BALANCE}."
            )

    def _validate_sufficient_funds(self, amount: float) -> None:
        if self._balance - amount < self.MIN_BALANCE:
            raise InsufficientBalanceError(
                f"Transfer would breach the minimum balance of Rs. {self.MIN_BALANCE}."
            )


class CurrentAccount(Account):
    """Current account: no minimum balance, but a fixed overdraft limit instead."""

    __mapper_args__ = {"polymorphic_identity": "CURRENT"}

    OVERDRAFT_LIMIT = 50000

    def calculate_withdrawal_limit(self) -> float:
        """Current accounts may withdraw balance PLUS the overdraft limit."""
        return max(self._balance + self.OVERDRAFT_LIMIT, 0)

    def _validate_withdrawal(self, amount: float) -> None:
        if self._balance - amount < -self.OVERDRAFT_LIMIT:
            raise InsufficientBalanceError(
                f"Withdrawal exceeds available balance plus overdraft limit of Rs. {self.OVERDRAFT_LIMIT}."
            )

    def _validate_sufficient_funds(self, amount: float) -> None:
        if self._balance - amount < -self.OVERDRAFT_LIMIT:
            raise InsufficientBalanceError(
                f"Transfer exceeds available balance plus overdraft limit of Rs. {self.OVERDRAFT_LIMIT}."
            )

    def get_withdrawal_fee(self) -> float:
        # Example of polymorphic fee behaviour: current accounts pay the same
        # base fee here, but the hook exists so fee rules can diverge per type.
        return WITHDRAWAL_FEE


class DailyLimitTracker(db.Model):
    """
    Persists how much an account has withdrawn/transferred on a given date,
    so limits survive an application restart instead of living only in memory.
    """

    __tablename__ = "daily_limit_trackers"

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey("accounts.id"), nullable=False)
    tracked_date = db.Column(db.Date, nullable=False, default=date.today)
    withdrawn_amount = db.Column(db.Float, nullable=False, default=0.0)
    transferred_amount = db.Column(db.Float, nullable=False, default=0.0)

    __table_args__ = (db.UniqueConstraint("account_id", "tracked_date", name="uq_account_date"),)
