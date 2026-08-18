# PyBank ATM System

A complete, class-based Object-Oriented ATM System built with **Python, Flask, and SQLAlchemy** on the backend and **HTML5 / CSS3 / vanilla JavaScript (Jinja2 templates)** on the frontend. Built as a learning/presentation project to demonstrate professional OOP design, secure banking logic, and a clean full-stack architecture — while remaining simple enough to run locally with a few PowerShell commands.

---

## 1. Project Description

PyBank ATM simulates a real ATM: a customer inserts a card, enters a PIN, is authenticated, chooses which account to operate on (if they have more than one), and can then deposit, withdraw, transfer, change their PIN, or view a mini statement — all backed by a real SQLite database, real password/PIN hashing, and real business rules (minimum balances, overdraft limits, daily withdrawal caps, ATM cash/denomination management, transaction fees, and card lockout after 3 failed PIN attempts).

---

## 2. Features

- Card + PIN authentication with a 3-attempt lockout (card becomes `BLOCKED`)
- Multi-account customers (Savings + Current) with in-session account switching
- Deposit, Withdraw, Transfer, Change PIN, Mini Statement, Logout
- Savings account: Rs. 5,000 minimum balance, Rs. 50,000 max withdrawal/transaction
- Current account: Rs. 50,000 overdraft limit
- ATM cash inventory (Rs. 500 / Rs. 1,000 / Rs. 5,000 notes) with real denomination-combination logic
- Persisted daily withdrawal/transfer limits (Rs. 100,000/day) that survive an app restart
- Transaction fees: Rs. 50 withdrawal fee, Rs. 100 transfer fee
- Full transaction history stored in SQLite, mini statement shows the last 5
- Hashed PINs (Werkzeug `generate_password_hash`) — plaintext PINs are never stored or logged
- CSRF-protected forms (Flask-WTF), server-side validation on every input
- Custom exception hierarchy with friendly, non-technical error messages
- 22 automated tests covering the core business logic

---

## 3. Technologies

**Backend:** Python 3, Flask, Flask-SQLAlchemy, Flask-WTF, SQLite, Werkzeug (PIN hashing)
**Frontend:** HTML5, CSS3, vanilla JavaScript, Jinja2 templates
**Testing:** pytest

---

## 4. OOP Concepts Demonstrated

| Concept | Where |
|---|---|
| **Encapsulation** | `Account._balance`, `Account._pin_hash`, `Account._status` (and the equivalents on `Card`) are exposed only via read-only properties or controlled methods. `account.balance = -50000` raises `AttributeError` — there is no setter. Balance only ever changes inside `deposit()`, `withdraw()`, `credit()`, `debit()`. PIN only ever changes inside `change_pin()`. |
| **Inheritance** | `Account` → `SavingsAccount` / `CurrentAccount`. `Transaction` → `DepositTransaction` / `WithdrawalTransaction` / `TransferTransaction`. |
| **Polymorphism** | `calculate_withdrawal_limit()` behaves differently for `SavingsAccount` (balance-above-minimum, capped at Rs. 50,000) vs. `CurrentAccount` (balance + Rs. 50,000 overdraft). `display_amount()` differs per `Transaction` subclass. |
| **Abstraction** | `Account.calculate_withdrawal_limit()`, `Account._validate_withdrawal()`, and `Account._validate_sufficient_funds()` are declared on the base class and raise `NotImplementedError` unless a subclass provides a real implementation — the base class defines the contract, not the behaviour. |
| **Constructors** | Each model uses an `initialize()`-style constructor helper (`Account.initialize()`, `Card.initialize()`) instead of allowing balance/PIN to be passed directly, keeping object creation controlled. |
| **Composition / Association** | `Customer` **has-many** `Account`s and `Card`s. `Account` **has-many** `Transaction`s. `ATM` **works-with** `CashDenomination` rows. `Bank` is a coordinating class that works with `Customer` and `Account`. |

---

## 5. Project Structure

```
atm_system/
│
├── app.py                     # Flask routes only — no business logic
├── config.py                  # App configuration
├── requirements.txt
├── README.md
├── .gitignore
│
├── models/
│   ├── __init__.py
│   ├── account.py             # Account, SavingsAccount, CurrentAccount, DailyLimitTracker
│   ├── customer.py            # Customer
│   ├── card.py                # Card (authentication, lockout)
│   ├── transaction.py         # Transaction, Deposit/Withdrawal/TransferTransaction
│   ├── atm.py                 # CashDenomination, ATM (cash/denomination logic)
│   └── bank.py                # Bank (lookup/authorization helpers)
│
├── services/
│   ├── auth_service.py        # Card/PIN login, account selection
│   ├── account_service.py     # Deposit/withdraw/transfer/change-pin orchestration
│   ├── transaction_service.py # Transaction record creation + mini statement
│   └── atm_service.py         # ATM instance + cash-commit helper
│
├── exceptions/
│   └── custom_exceptions.py   # InvalidPINError, CardBlockedError, InsufficientBalanceError, ...
│
├── database/
│   ├── db.py                  # Shared SQLAlchemy instance
│   └── seed.py                # Sample data generator
│
├── templates/                 # Jinja2 templates (login, dashboard, balance, deposit, ...)
├── static/
│   ├── css/style.css
│   └── js/script.js
│
└── tests/
    └── test_atm.py            # 22 tests covering all core business rules
```

---

## 6. Installation (Windows PowerShell)

```powershell
# 1. Navigate into the project folder
cd atm_system

# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Seed the database with sample data
python -m database.seed

# 5. Run the application
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

> The first run of `app.py` also calls `db.create_all()` automatically, so if you skip step 4 the app will still start — but you'll need to seed the database (step 4) to have any customers/cards/cash to log in with.

---

## 7. Demo Credentials

Card numbers are randomly generated each time you run the seed script — after running `python -m database.seed`, the exact **Card Number** for each demo customer is printed to the console. Example output:

```
Demo credentials:
  Ali Khan   -> Card: <16-digit number>  PIN: 1234  (Savings only)
  Sara Ahmed -> Card: <16-digit number>  PIN: 4321  (Savings + Current)
```

Use the printed card number with the listed PIN to log in. (Card numbers are randomized on every seed run instead of being hardcoded, so no real-looking secret ever lives in the source code.)

---

## 8. How the ATM Works

```
Open the app  →  Insert Card (enter card number + PIN)
                       ↓
        Card validated, PIN validated (3-attempt lockout)
                       ↓
   Select account (if customer has more than one)
                       ↓
                  ATM Dashboard
                       ↓
     Check Balance / Deposit / Withdraw / Transfer /
            Change PIN / Mini Statement
                       ↓
        Backend validates everything server-side
                       ↓
          Transaction processed & recorded
                       ↓
        Result / receipt shown → back to Dashboard
                       ↓
                     Logout
```

### Withdrawal flow specifically:
1. Account must be `ACTIVE`.
2. Amount must be between Rs. 500 and Rs. 50,000.
3. Daily withdrawal total (persisted in `daily_limit_trackers`, keyed by date) must stay under Rs. 100,000.
4. The ATM must be able to represent the amount using its available Rs. 500 / Rs. 1,000 / Rs. 5,000 notes (`ATM.calculate_note_combination()`), checked **before** the balance is touched.
5. The account must have sufficient balance (respecting the minimum balance / overdraft rule for its type).
6. Only after all checks pass: balance is debited, ATM notes are deducted, the daily tracker is updated, and a `WithdrawalTransaction` is recorded — all in one commit.

---

## 9. Security Features

- PINs are never stored or logged in plaintext — only Werkzeug password hashes.
- `balance`, `status`, and PIN fields have **no public setter**; they can only change through the model's own methods.
- Card locks after 3 consecutive failed PIN attempts and stays locked (further attempts, even with the correct PIN, are rejected).
- Changing a PIN re-verifies the current PIN, validates the new PIN (4 digits), and requires confirmation before hashing and storing it — and keeps the card's login PIN in sync.
- Every account access goes through `Bank.ensure_owned_by()`, so one customer can never operate on another customer's account, even by guessing an account number.
- All money amounts and account ownership are validated server-side — frontend validation is UX-only and is never trusted.
- CSRF tokens (Flask-WTF) are required on every state-changing form.
- SQL injection is not possible through normal use — all queries go through the SQLAlchemy ORM (parameterized queries).
- Custom exceptions produce friendly messages; raw Python tracebacks are never shown to the user (see the `404`/`500` handlers in `app.py`).
- Session cookies are `HttpOnly` and `SameSite=Lax`.

---

## 10. Testing

Run the full test suite from the project root:

```powershell
pytest -v
```

The suite (`tests/test_atm.py`, 22 tests) covers: correct/incorrect PIN, card blocking after 3 failures, deposits (valid/invalid), withdrawals (valid, insufficient balance, per-transaction limit, daily limit, ATM insufficient cash, unsupported denomination amounts), transfers (valid, invalid receiver, same sender/receiver), PIN changes (valid/invalid current PIN), mini statement, Savings minimum-balance rule, Current account overdraft, and both transaction fees.

---

## 11. Requirements Checklist

- [x] All required classes implemented: `Account`, `SavingsAccount`, `CurrentAccount`, `Customer`, `Card`, `Transaction`, `DepositTransaction`, `WithdrawalTransaction`, `TransferTransaction`, `ATM`, `Bank`
- [x] Encapsulation, inheritance, polymorphism, abstraction, constructors, and class relationships all demonstrated
- [x] Card authentication flow with 3-attempt lockout
- [x] PINs hashed, never stored/logged/exposed in plaintext
- [x] Full ATM dashboard (Balance, Deposit, Withdraw, Transfer, Change PIN, Mini Statement, Logout)
- [x] Withdrawal business rules (min/max, daily limit, ATM cash check, denomination combination)
- [x] ATM cash/denomination management, dynamically updated
- [x] Deposit with transaction ID + timestamp
- [x] Money transfer with validation + two transaction records + Rs. 100 fee
- [x] Transaction system with base + child classes, stored in SQLite
- [x] Rs. 50 withdrawal fee / Rs. 100 transfer fee
- [x] Mini statement (last 5 transactions, from the database)
- [x] Daily limits persisted (survive app restart)
- [x] Account status (`ACTIVE` / `BLOCKED` / `INACTIVE`) enforced before every transaction
- [x] Custom exception hierarchy, friendly error messages, no stack traces shown
- [x] SQLite with proper relationships and unique constraints
- [x] Security: hashed PINs, sessions, CSRF, server-side validation, authorization checks, no direct balance/PIN mutation
- [x] Responsive, professional ATM-style frontend
- [x] Sample data seed script with documented demo credentials
- [x] 22 automated tests covering the required scenarios
- [x] This README

---

## 12. Notes

- `SECRET_KEY` in `config.py` defaults to a development value — set the `ATM_SECRET_KEY` environment variable before any real deployment.
- This is an educational project; the Flask development server (`app.run()`) is not intended for production use.
