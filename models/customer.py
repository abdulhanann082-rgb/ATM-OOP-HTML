"""
Customer model.

Demonstrates composition/association: a Customer HAS-MANY Accounts and
HAS-MANY Cards. A customer can hold both a SavingsAccount and a
CurrentAccount at the same time and choose which one to operate on.
"""

from __future__ import annotations

import random
import string
from datetime import datetime

from database.db import db


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    accounts = db.relationship("Account", backref="customer", lazy=True)
    cards = db.relationship("Card", backref="customer", lazy=True)

    @staticmethod
    def generate_customer_id() -> str:
        return "CUST-" + "".join(random.choices(string.digits, k=6))

    def get_account_by_number(self, account_number: str):
        """Return one of THIS customer's accounts, or None (used for authorization checks)."""
        return next((a for a in self.accounts if a.account_number == account_number), None)

    def __repr__(self) -> str:
        return f"<Customer {self.customer_id} {self.name}>"
