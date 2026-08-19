"""ATMService - thin wrapper that gives the rest of the app a fresh ATM
instance (backed by the current CashDenomination rows) and commits any
cash changes it makes."""

from __future__ import annotations

from database.db import db
from models.atm import ATM


class ATMService:
    @staticmethod
    def get_atm() -> ATM:
        return ATM()

    @staticmethod
    def commit_cash_changes() -> None:
        db.session.commit()
