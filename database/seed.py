"""
Seed script - populates the database with sample data for testing/demo.

Run with:  python -m database.seed
(or it is called automatically the first time app.py finds an empty DB)
"""

from __future__ import annotations

from datetime import datetime, timedelta

from app import app
from database.db import db
from models import (
    Customer,
    Card,
    SavingsAccount,
    CurrentAccount,
    CashDenomination,
)
from services.transaction_service import TransactionService


def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()

        # ---------------- Customer 1: Ali Khan (Savings) ---------------- #
        ali = Customer(customer_id=Customer.generate_customer_id(), name="Ali Khan",
                        phone="0300-1234567", email="ali.khan@example.com")
        db.session.add(ali)
        db.session.flush()

        ali_savings = SavingsAccount(customer_id=ali.id)
        ali_savings.initialize(pin="1234", opening_balance=75000)
        db.session.add(ali_savings)
        db.session.flush()

        ali_card = Card(customer_id=ali.id)
        ali_card.initialize(pin="1234")
        db.session.add(ali_card)

        # ---------------- Customer 2: Sara Ahmed (Savings + Current) ---------------- #
        sara = Customer(customer_id=Customer.generate_customer_id(), name="Sara Ahmed",
                         phone="0301-7654321", email="sara.ahmed@example.com")
        db.session.add(sara)
        db.session.flush()

        sara_savings = SavingsAccount(customer_id=sara.id)
        sara_savings.initialize(pin="4321", opening_balance=50000)
        db.session.add(sara_savings)

        sara_current = CurrentAccount(customer_id=sara.id)
        sara_current.initialize(pin="4321", opening_balance=20000)
        db.session.add(sara_current)
        db.session.flush()

        sara_card = Card(customer_id=sara.id)
        sara_card.initialize(pin="4321")
        db.session.add(sara_card)

        db.session.flush()

        # ---------------- ATM cash inventory ---------------- #
        db.session.add(CashDenomination(note_value=500, quantity=20))
        db.session.add(CashDenomination(note_value=1000, quantity=30))
        db.session.add(CashDenomination(note_value=5000, quantity=10))

        # ---------------- Sample transactions for Ali ---------------- #
        t1 = TransactionService.record_deposit(ali_savings, 20000, ali_savings.balance)
        t1.timestamp = datetime.utcnow() - timedelta(days=3)

        t2 = TransactionService.record_withdrawal(ali_savings, 10000, 50, ali_savings.balance)
        t2.timestamp = datetime.utcnow() - timedelta(days=2)

        t3 = TransactionService.record_deposit(ali_savings, 30000, ali_savings.balance)
        t3.timestamp = datetime.utcnow() - timedelta(days=1)

        db.session.commit()

        print("Database seeded successfully.\n")
        print("Demo credentials:")
        print(f"  Ali Khan   -> Card: {ali_card.card_number}  PIN: 1234  (Savings only)")
        print(f"  Sara Ahmed -> Card: {sara_card.card_number}  PIN: 4321  (Savings + Current)")


if __name__ == "__main__":
    seed()
