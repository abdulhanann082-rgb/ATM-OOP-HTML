"""
Test suite for the ATM system's business logic.

Run with (from the project root):
    pytest -v

Each test gets a fresh in-memory SQLite database via the `app_ctx` fixture,
so tests never depend on each other or on atm_system.db.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from app import app as flask_app
from database.db import db
from models import (
    Customer,
    Card,
    SavingsAccount,
    CurrentAccount,
    CashDenomination,
)
from services.auth_service import AuthService
from services.account_service import AccountService
from exceptions.custom_exceptions import (
    InvalidPINError,
    CardBlockedError,
    InsufficientBalanceError,
    InsufficientATMFundsError,
    InvalidAmountError,
    DailyLimitExceededError,
    SameAccountTransferError,
    DenominationError,
)


@pytest.fixture()
def app_ctx():
    flask_app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


def make_customer(name="Test User"):
    customer = Customer(customer_id=Customer.generate_customer_id(), name=name)
    db.session.add(customer)
    db.session.flush()
    return customer


def make_savings_account(customer, pin="1111", balance=20000):
    account = SavingsAccount(customer_id=customer.id)
    account.initialize(pin=pin, opening_balance=balance)
    db.session.add(account)
    db.session.flush()
    return account


def make_current_account(customer, pin="2222", balance=5000):
    account = CurrentAccount(customer_id=customer.id)
    account.initialize(pin=pin, opening_balance=balance)
    db.session.add(account)
    db.session.flush()
    return account


def make_card(customer, pin="1111"):
    card = Card(customer_id=customer.id)
    card.initialize(pin=pin)
    db.session.add(card)
    db.session.flush()
    return card


def seed_atm_cash(cash_500=20, cash_1000=30, cash_5000=10):
    db.session.add(CashDenomination(note_value=500, quantity=cash_500))
    db.session.add(CashDenomination(note_value=1000, quantity=cash_1000))
    db.session.add(CashDenomination(note_value=5000, quantity=cash_5000))
    db.session.commit()


# --------------------------------------------------------------------- #
# Card authentication
# --------------------------------------------------------------------- #
class TestCardAuthentication:
    def test_correct_pin_logs_in(self, app_ctx):
        customer = make_customer()
        card = make_card(customer, pin="1111")
        db.session.commit()

        result = AuthService.login(card.card_number, "1111")
        assert result.id == customer.id

    def test_incorrect_pin_raises(self, app_ctx):
        customer = make_customer()
        card = make_card(customer, pin="1111")
        db.session.commit()

        with pytest.raises(InvalidPINError):
            AuthService.login(card.card_number, "9999")

    def test_card_blocked_after_three_failures(self, app_ctx):
        customer = make_customer()
        card = make_card(customer, pin="1111")
        db.session.commit()

        for _ in range(2):
            with pytest.raises(InvalidPINError):
                AuthService.login(card.card_number, "0000")

        with pytest.raises(CardBlockedError):
            AuthService.login(card.card_number, "0000")

        # Even the correct PIN must now fail.
        with pytest.raises(CardBlockedError):
            AuthService.login(card.card_number, "1111")


# --------------------------------------------------------------------- #
# Deposit
# --------------------------------------------------------------------- #
class TestDeposit:
    def test_deposit_increases_balance(self, app_ctx):
        customer = make_customer()
        account = make_savings_account(customer, balance=20000)
        db.session.commit()

        AccountService.deposit(account, 10000)
        assert account.balance == 30000

    def test_invalid_deposit_amount_raises(self, app_ctx):
        customer = make_customer()
        account = make_savings_account(customer, balance=20000)
        db.session.commit()

        with pytest.raises(InvalidAmountError):
            AccountService.deposit(account, -500)


# --------------------------------------------------------------------- #
# Withdrawal
# --------------------------------------------------------------------- #
class TestWithdrawal:
    def test_successful_withdrawal(self, app_ctx):
        customer = make_customer()
        account = make_savings_account(customer, balance=20000)
        seed_atm_cash()
        db.session.commit()

        txn, plan = AccountService.withdraw(account, 5000)
        assert account.balance == 20000 - 5000 - 50  # amount + fee
        assert sum(note * count for note, count in plan.items()) == 5000

    def test_insufficient_balance(self, app_ctx):
        customer = make_customer()
        account = make_savings_account(customer, balance=5500)  # near min balance
        seed_atm_cash()
        db.session.commit()

        with pytest.raises(InsufficientBalanceError):
            AccountService.withdraw(account, 2000)

    def test_withdrawal_limit_per_transaction(self, app_ctx):
        customer = make_customer()
        account = make_savings_account(customer, balance=200000)
        seed_atm_cash(cash_500=1000, cash_1000=1000, cash_5000=1000)
        db.session.commit()

        with pytest.raises(InvalidAmountError):
            AccountService.withdraw(account, 60000)  # > MAX_WITHDRAWAL_PER_TRANSACTION

    def test_daily_withdrawal_limit(self, app_ctx):
        customer = make_customer()
        account = make_savings_account(customer, balance=500000)
        seed_atm_cash(cash_500=1000, cash_1000=1000, cash_5000=1000)
        db.session.commit()

        # Withdraw the max per-transaction amount twice (100,000 total is fine),
        # a third would exceed the 100,000 daily cap.
        AccountService.withdraw(account, 50000)
        AccountService.withdraw(account, 50000)

        with pytest.raises(DailyLimitExceededError):
            AccountService.withdraw(account, 1000)

    def test_atm_insufficient_cash(self, app_ctx):
        customer = make_customer()
        account = make_savings_account(customer, balance=100000)
        seed_atm_cash(cash_500=1, cash_1000=0, cash_5000=0)  # only Rs. 500 in the machine
        db.session.commit()

        with pytest.raises(InsufficientATMFundsError):
            AccountService.withdraw(account, 5000)

        # Balance must be untouched since the ATM couldn't dispense.
        assert account.balance == 100000

    def test_unsupported_denomination_amount(self, app_ctx):
        customer = make_customer()
        account = make_savings_account(customer, balance=100000)
        seed_atm_cash()
        db.session.commit()

        with pytest.raises((DenominationError, InvalidAmountError)):
            AccountService.withdraw(account, 700)  # not representable / below granularity


# --------------------------------------------------------------------- #
# Transfer
# --------------------------------------------------------------------- #
class TestTransfer:
    def test_successful_transfer(self, app_ctx):
        customer1 = make_customer("Sender")
        customer2 = make_customer("Receiver")
        sender = make_savings_account(customer1, pin="1111", balance=20000)
        receiver = make_savings_account(customer2, pin="2222", balance=10000)
        db.session.commit()

        AccountService.transfer(sender, receiver.account_number, 5000)

        assert sender.balance == 20000 - 5000 - 100  # amount + fee
        assert receiver.balance == 15000

    def test_invalid_receiver_account(self, app_ctx):
        customer = make_customer()
        sender = make_savings_account(customer, balance=20000)
        db.session.commit()

        with pytest.raises(Exception):
            AccountService.transfer(sender, "0000000000", 1000)

    def test_same_sender_receiver(self, app_ctx):
        customer = make_customer()
        sender = make_savings_account(customer, balance=20000)
        db.session.commit()

        with pytest.raises(SameAccountTransferError):
            AccountService.transfer(sender, sender.account_number, 1000)


# --------------------------------------------------------------------- #
# Change PIN
# --------------------------------------------------------------------- #
class TestChangePin:
    def test_change_pin_success(self, app_ctx):
        customer = make_customer()
        account = make_savings_account(customer, pin="1111", balance=20000)
        db.session.commit()

        card = make_card(customer, pin="1111")
        db.session.commit()
        AccountService.change_pin(account, card, "1111", "2222", "2222")
        assert account.verify_pin("2222")
        assert not account.verify_pin("1111")
        # Card's login PIN must stay in sync with the account's PIN.
        card.authenticate("2222")

    def test_change_pin_wrong_current(self, app_ctx):
        customer = make_customer()
        account = make_savings_account(customer, pin="1111", balance=20000)
        db.session.commit()

        with pytest.raises(InvalidPINError):
            AccountService.change_pin(account, None, "0000", "2222", "2222")


# --------------------------------------------------------------------- #
# Mini statement
# --------------------------------------------------------------------- #
class TestMiniStatement:
    def test_mini_statement_returns_recent_transactions(self, app_ctx):
        customer = make_customer()
        account = make_savings_account(customer, balance=20000)
        seed_atm_cash()
        db.session.commit()

        for _ in range(6):
            AccountService.deposit(account, 1000)

        statement = AccountService.mini_statement(account, limit=5)
        assert len(statement) == 5


# --------------------------------------------------------------------- #
# Account-type rules & polymorphism
# --------------------------------------------------------------------- #
class TestAccountRules:
    def test_savings_minimum_balance_enforced(self, app_ctx):
        customer = make_customer()
        account = make_savings_account(customer, balance=5500)
        seed_atm_cash()
        db.session.commit()

        with pytest.raises(InsufficientBalanceError):
            AccountService.withdraw(account, 1000)  # would breach Rs. 5,000 minimum

    def test_current_account_overdraft(self, app_ctx):
        customer = make_customer()
        account = make_current_account(customer, balance=1000)
        seed_atm_cash(cash_500=1000, cash_1000=1000, cash_5000=1000)
        db.session.commit()

        # Balance 1000 -> withdraw 20000 + 50 fee => goes negative but within
        # the Rs. 50,000 overdraft limit.
        AccountService.withdraw(account, 20000)
        assert account.balance == 1000 - 20000 - 50

    def test_polymorphic_withdrawal_limit(self, app_ctx):
        customer = make_customer()
        savings = make_savings_account(customer, balance=100000)
        current = make_current_account(customer, pin="2222", balance=1000)
        db.session.commit()

        # Different account types compute different limits for the same call.
        assert savings.calculate_withdrawal_limit() != current.calculate_withdrawal_limit()
        assert savings.calculate_withdrawal_limit() == 50000  # capped by MAX_WITHDRAWAL
        assert current.calculate_withdrawal_limit() == 1000 + 50000


# --------------------------------------------------------------------- #
# Fees
# --------------------------------------------------------------------- #
class TestFees:
    def test_withdrawal_fee_deducted(self, app_ctx):
        customer = make_customer()
        account = make_savings_account(customer, balance=20000)
        seed_atm_cash()
        db.session.commit()

        AccountService.withdraw(account, 1000)
        assert account.balance == 20000 - 1000 - 50

    def test_transfer_fee_deducted(self, app_ctx):
        customer1 = make_customer("A")
        customer2 = make_customer("B")
        sender = make_savings_account(customer1, pin="1111", balance=20000)
        receiver = make_savings_account(customer2, pin="2222", balance=10000)
        db.session.commit()

        AccountService.transfer(sender, receiver.account_number, 1000)
        assert sender.balance == 20000 - 1000 - 100
        assert receiver.balance == 11000  # receiver pays no fee
