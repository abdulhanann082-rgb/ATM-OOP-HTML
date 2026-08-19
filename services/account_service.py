"""
AccountService - the main orchestration layer.

Flask routes call INTO this service; the service calls the OOP model
methods (Account.deposit/withdraw/credit/debit, ATM.dispense, etc.) and
the TransactionService, then commits everything as one unit of work.

Keeping this logic out of app.py satisfies the "separate business logic
from Flask routes" requirement and keeps routes thin and readable.
"""

from __future__ import annotations

from datetime import date

from database.db import db
from models.account import Account, DAILY_WITHDRAWAL_LIMIT, TRANSFER_FEE, MIN_WITHDRAWAL_AMOUNT, MAX_WITHDRAWAL_PER_TRANSACTION
from models.bank import Bank
from models.atm import ATM
from services.transaction_service import TransactionService
from services.atm_service import ATMService
from exceptions.custom_exceptions import (
    InvalidAmountError,
    InsufficientBalanceError,
    DailyLimitExceededError,
    SameAccountTransferError,
    InvalidAccountError,
)


class AccountService:
    # ------------------------------------------------------------------ #
    # Balance / statement
    # ------------------------------------------------------------------ #
    @staticmethod
    def check_balance(account: Account) -> float:
        return account.check_balance()

    @staticmethod
    def mini_statement(account: Account, limit: int = 5) -> list:
        return TransactionService.get_mini_statement(account, limit)

    # ------------------------------------------------------------------ #
    # Deposit
    # ------------------------------------------------------------------ #
    @staticmethod
    def deposit(account: Account, amount: float):
        account.deposit(amount)  # validates + credits balance
        txn = TransactionService.record_deposit(account, amount, account.balance)
        db.session.commit()
        return txn

    # ------------------------------------------------------------------ #
    # Withdrawal
    # ------------------------------------------------------------------ #
    @staticmethod
    def withdraw(account: Account, amount: float):
        account.ensure_active()

        if amount <= 0:
            raise InvalidAmountError("Withdrawal amount must be positive.")
        if amount < MIN_WITHDRAWAL_AMOUNT:
            raise InvalidAmountError(f"Withdrawal amount must be at least Rs. {MIN_WITHDRAWAL_AMOUNT}.")
        if amount > MAX_WITHDRAWAL_PER_TRANSACTION:
            raise InvalidAmountError(
                f"Withdrawal amount cannot exceed Rs. {MAX_WITHDRAWAL_PER_TRANSACTION} per transaction."
            )

        # 1) Daily withdrawal limit check (persisted, resets automatically per day)
        tracker = account.get_or_create_today_tracker()
        if tracker.withdrawn_amount + amount > DAILY_WITHDRAWAL_LIMIT:
            remaining = max(DAILY_WITHDRAWAL_LIMIT - tracker.withdrawn_amount, 0)
            raise DailyLimitExceededError(
                f"Daily withdrawal limit exceeded. You can withdraw up to Rs. {remaining:,.0f} more today."
            )

        # 2) Confirm the ATM CAN physically dispense this amount before
        #    touching the account balance at all.
        atm = ATMService.get_atm()
        note_plan = atm.calculate_note_combination(int(amount))  # raises if not possible

        # 3) Validate + debit the account (raises InsufficientBalanceError etc.)
        fee = account.get_withdrawal_fee()
        account.withdraw(amount, fee=fee)

        # 4) Only now mutate the ATM's physical cash inventory.
        atm.dispense(int(amount))

        # 5) Update the persisted daily tracker.
        tracker.withdrawn_amount += amount

        # 6) Record the transaction.
        txn = TransactionService.record_withdrawal(account, amount, fee, account.balance)

        db.session.commit()
        return txn, note_plan

    # ------------------------------------------------------------------ #
    # Transfer
    # ------------------------------------------------------------------ #
    @staticmethod
    def transfer(sender: Account, receiver_account_number: str, amount: float):
        if amount <= 0:
            raise InvalidAmountError("Transfer amount must be positive.")

        sender.ensure_active()

        receiver = Bank.find_account_by_number(receiver_account_number)
        if receiver is None:
            raise InvalidAccountError("Receiver account not found.")

        if sender.account_number == receiver.account_number:
            raise SameAccountTransferError("Sender and receiver accounts cannot be the same.")

        receiver.ensure_active()

        tracker = sender.get_or_create_today_tracker()
        # Reuse the withdrawal daily cap for outgoing transfers as well.
        if tracker.transferred_amount + amount > DAILY_WITHDRAWAL_LIMIT:
            raise DailyLimitExceededError("Daily transfer limit exceeded.")

        fee = sender.get_transfer_fee()
        total_debit = amount + fee

        # Debit sender first (raises InsufficientBalanceError if not enough funds).
        sender.debit(total_debit)
        # Credit receiver.
        receiver.credit(amount)

        tracker.transferred_amount += amount

        sender_txn = TransactionService.record_transfer(
            sender, amount, fee, sender.balance, receiver.account_number, note="Money sent"
        )
        receiver_txn = TransactionService.record_transfer(
            receiver, amount, 0.0, receiver.balance, sender.account_number, note="Money received"
        )

        db.session.commit()
        return sender_txn, receiver_txn

    # ------------------------------------------------------------------ #
    # Change PIN
    # ------------------------------------------------------------------ #
    @staticmethod
    def change_pin(account: Account, card, current_pin: str, new_pin: str, confirm_pin: str):
        """
        Change the PIN.

        The customer only perceives a single "PIN" (the one they type at
        login), so this keeps the Account's own PIN and the linked Card's
        login PIN in sync: Account.change_pin() does the real verification
        and validation, then the Card's hash is updated to match.
        """
        account.change_pin(current_pin, new_pin, confirm_pin)
        if card is not None:
            card.sync_pin_from_plain(new_pin)
        db.session.commit()
