"""
Custom exception hierarchy for the ATM system.

Using specific exceptions instead of generic ones lets the service layer
communicate exactly what went wrong, and lets the Flask routes translate
each one into a clean, user-friendly message (never a raw traceback).
"""


class ATMException(Exception):
    """Base class for all ATM-related exceptions."""

    def __init__(self, message: str = "An ATM error occurred."):
        self.message = message
        super().__init__(self.message)


class InvalidPINError(ATMException):
    """Raised when a PIN does not match the stored (hashed) PIN."""

    def __init__(self, message: str = "Invalid PIN."):
        super().__init__(message)


class CardBlockedError(ATMException):
    """Raised when a blocked card attempts authentication or a transaction."""

    def __init__(self, message: str = "This card has been blocked."):
        super().__init__(message)


class InsufficientBalanceError(ATMException):
    """Raised when an account does not have enough balance for an operation."""

    def __init__(self, message: str = "Insufficient balance."):
        super().__init__(message)


class InsufficientATMFundsError(ATMException):
    """Raised when the ATM's cash inventory cannot fulfil a withdrawal."""

    def __init__(self, message: str = "ATM has insufficient cash. Please try another amount."):
        super().__init__(message)


class InvalidAmountError(ATMException):
    """Raised when an amount is zero, negative, or otherwise invalid."""

    def __init__(self, message: str = "Invalid amount."):
        super().__init__(message)


class AccountInactiveError(ATMException):
    """Raised when a transaction is attempted on a non-active account."""

    def __init__(self, message: str = "Account is not active."):
        super().__init__(message)


class DailyLimitExceededError(ATMException):
    """Raised when a daily withdrawal/transfer limit would be exceeded."""

    def __init__(self, message: str = "Daily limit exceeded."):
        super().__init__(message)


class InvalidAccountError(ATMException):
    """Raised when an account number does not exist or is otherwise invalid."""

    def __init__(self, message: str = "Invalid account number."):
        super().__init__(message)


class DenominationError(ATMException):
    """Raised when the ATM cannot represent the requested amount with its notes."""

    def __init__(self, message: str = "ATM cannot dispense this amount with available denominations."):
        super().__init__(message)


class UnauthorizedAccessError(ATMException):
    """Raised when a customer attempts to access an account that is not theirs."""

    def __init__(self, message: str = "You are not authorized to access this account."):
        super().__init__(message)


class SameAccountTransferError(ATMException):
    """Raised when sender and receiver accounts are identical in a transfer."""

    def __init__(self, message: str = "Sender and receiver accounts cannot be the same."):
        super().__init__(message)
