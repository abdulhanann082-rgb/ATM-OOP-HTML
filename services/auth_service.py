"""
AuthService - handles the "Insert Card -> Enter PIN -> Validate Card ->
Validate PIN -> Dashboard" flow, plus account selection for customers
that hold more than one account.
"""

from __future__ import annotations

from database.db import db
from models.card import Card
from models.customer import Customer
from models.account import Account
from exceptions.custom_exceptions import (
    InvalidAccountError,
    CardBlockedError,
    InvalidPINError,
    UnauthorizedAccessError,
)


class AuthService:
    @staticmethod
    def login(card_number: str, pin: str) -> Customer:
        """Validate the card + PIN. Returns the authenticated Customer.

        Raises InvalidAccountError / CardBlockedError / InvalidPINError on failure.
        """
        card = Card.query.filter_by(card_number=card_number).first()
        if card is None:
            raise InvalidAccountError("Card not found.")

        try:
            card.authenticate(pin)
        finally:
            # Persist failed_attempts / BLOCKED status regardless of outcome.
            db.session.commit()

        return Customer.query.get(card.customer_id)

    @staticmethod
    def select_account(customer: Customer, account_number: str) -> Account:
        """Let the customer choose which of their accounts to operate on."""
        account = customer.get_account_by_number(account_number)
        if account is None:
            raise UnauthorizedAccessError("That account does not belong to this customer.")
        account.ensure_active()
        return account

    @staticmethod
    def get_customer_accounts(customer: Customer) -> list[Account]:
        return list(customer.accounts)
