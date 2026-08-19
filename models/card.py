"""
Card model - represents the physical ATM card used to authenticate.

The card's own PIN is what a customer enters at "Insert Card -> Enter PIN".
After 3 wrong attempts the card status becomes BLOCKED and no further
transactions are allowed with it, regardless of which account is chosen.
"""

from __future__ import annotations

import random
import string
from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash

from database.db import db
from exceptions.custom_exceptions import InvalidPINError, CardBlockedError

MAX_PIN_ATTEMPTS = 3


class Card(db.Model):
    __tablename__ = "cards"

    id = db.Column(db.Integer, primary_key=True)
    card_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)

    _pin_hash = db.Column("pin_hash", db.String(255), nullable=False)
    _status = db.Column("status", db.String(20), nullable=False, default="ACTIVE")
    _failed_attempts = db.Column("failed_attempts", db.Integer, nullable=False, default=0)

    issued_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def status(self) -> str:
        return self._status

    @property
    def failed_attempts(self) -> int:
        return self._failed_attempts

    def initialize(self, pin: str) -> None:
        self.card_number = self._generate_card_number()
        self._pin_hash = generate_password_hash(pin)
        self._status = "ACTIVE"
        self._failed_attempts = 0

    @staticmethod
    def _generate_card_number() -> str:
        return "".join(random.choices(string.digits, k=16))

    def authenticate(self, pin: str) -> None:
        """
        Validate the entered PIN.

        Raises CardBlockedError if the card is already blocked, or
        InvalidPINError (with remaining-attempts info) on a wrong PIN.
        Blocks the card automatically after MAX_PIN_ATTEMPTS failures.
        """
        if self._status == "BLOCKED":
            raise CardBlockedError("This card has been blocked due to too many failed PIN attempts.")

        if check_password_hash(self._pin_hash, pin):
            self._failed_attempts = 0
            return

        self._failed_attempts += 1
        if self._failed_attempts >= MAX_PIN_ATTEMPTS:
            self._status = "BLOCKED"
            raise CardBlockedError("Your card has been blocked after 3 failed PIN attempts.")

        remaining = MAX_PIN_ATTEMPTS - self._failed_attempts
        raise InvalidPINError(f"Invalid PIN. You have {remaining} attempt(s) remaining.")

    def sync_pin_from_plain(self, new_pin: str) -> None:
        """
        Keep the card's login PIN in sync with the linked account's PIN.

        Intended to be called ONLY by the service layer, immediately after
        Account.change_pin() has already verified/validated the new PIN -
        this method does not re-verify anything itself.
        """
        self._pin_hash = generate_password_hash(new_pin)

    def __repr__(self) -> str:
        last4 = self.card_number[-4:] if self.card_number else "----"
        return f"<Card ****{last4} status={self._status}>"
