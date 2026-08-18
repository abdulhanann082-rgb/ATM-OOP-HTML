"""
Bank - a plain domain class representing the institution itself.

It is not a database row (a single-bank system doesn't need one), but it
demonstrates composition: the Bank works with Customers and Accounts and
provides lookup/authorization helpers used across the service layer.
"""

from __future__ import annotations

from database.db import db
from models.customer import Customer
from models.account import Account
from models.card import Card
from exceptions.custom_exceptions import InvalidAccountError, UnauthorizedAccessError


class Bank:
    name = "PyBank"

    @staticmethod
    def find_customer_by_customer_id(customer_id: str) -> Customer | None:
        return Customer.query.filter_by(customer_id=customer_id).first()

    @staticmethod
    def find_card_by_number(card_number: str) -> Card | None:
        return Card.query.filter_by(card_number=card_number).first()

    @staticmethod
    def find_account_by_number(account_number: str) -> Account:
        account = Account.query.filter_by(account_number=account_number).first()
        if account is None:
            raise InvalidAccountError("Invalid account number.")
        return account

    @staticmethod
    def find_card_for_customer(customer: Customer) -> Card | None:
        """A customer may have more than one card in principle; the demo
        seed data gives each customer exactly one, so the first is used."""
        return Card.query.filter_by(customer_id=customer.id).first()

    @staticmethod
    def ensure_owned_by(account: Account, customer: Customer) -> None:
        """Authorization check: a customer may only operate on their own accounts."""
        if account.customer_id != customer.id:
            raise UnauthorizedAccessError("You are not authorized to access this account.")

    @staticmethod
    def total_deposits() -> float:
        return sum(a.balance for a in Account.query.all())
