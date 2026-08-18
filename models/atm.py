"""
ATM cash management.

CashDenomination is the persisted note inventory (SQLite table).
ATM is a plain domain class (not itself a DB row) that wraps that
inventory with the business logic for checking and dispensing cash -
demonstrating composition ("ATM works with denominations").
"""

from __future__ import annotations

from database.db import db
from exceptions.custom_exceptions import InsufficientATMFundsError, DenominationError

SUPPORTED_DENOMINATIONS = [5000, 1000, 500]


class CashDenomination(db.Model):
    __tablename__ = "atm_cash"

    id = db.Column(db.Integer, primary_key=True)
    note_value = db.Column(db.Integer, unique=True, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)

    @property
    def subtotal(self) -> int:
        return self.note_value * self.quantity


class ATM:
    """
    Wraps the CashDenomination rows for a single ATM machine.

    Given an amount, it works out whether the amount can be represented
    using the available notes (a greedy largest-note-first strategy),
    without ever mutating the database until the caller commits a
    successful withdrawal.
    """

    def __init__(self):
        self._denominations = {
            d.note_value: d for d in CashDenomination.query.all()
        }

    def total_cash(self) -> int:
        return sum(d.subtotal for d in self._denominations.values())

    def calculate_note_combination(self, amount: int) -> dict[int, int]:
        """
        Greedily pick the largest notes first. Returns {note_value: count}.
        Raises DenominationError if the amount cannot be represented at all
        with the supported denominations, or InsufficientATMFundsError if
        the machine simply doesn't have enough of the right notes.
        """
        if amount <= 0 or amount % 100 != 0:
            raise DenominationError("Amount must be a positive multiple of Rs. 100.")

        remaining = amount
        plan: dict[int, int] = {}

        for note in sorted(SUPPORTED_DENOMINATIONS, reverse=True):
            available = self._denominations.get(note)
            available_qty = available.quantity if available else 0
            if remaining <= 0:
                break
            needed = remaining // note
            used = min(needed, available_qty)
            if used > 0:
                plan[note] = used
                remaining -= used * note

        if remaining > 0:
            # Try to see if it's even theoretically representable (ignoring stock)
            # to give a clearer error message.
            if not self._is_theoretically_representable(amount):
                raise DenominationError(
                    "ATM cannot dispense this exact amount with Rs. 500/1000/5000 notes."
                )
            raise InsufficientATMFundsError("ATM has insufficient cash. Please try another amount.")

        return plan

    @staticmethod
    def _is_theoretically_representable(amount: int) -> bool:
        # With 500 as the smallest note, any positive multiple of 500 works.
        return amount % 500 == 0

    def has_sufficient_cash(self, amount: int) -> bool:
        try:
            self.calculate_note_combination(amount)
            return True
        except (InsufficientATMFundsError, DenominationError):
            return False

    def dispense(self, amount: int) -> dict[int, int]:
        """Compute the plan AND commit the note deduction. Call only after
        the account withdrawal itself has been validated, so cash is never
        deducted for a transaction that ultimately fails."""
        plan = self.calculate_note_combination(amount)
        for note_value, count in plan.items():
            self._denominations[note_value].quantity -= count
        return plan
