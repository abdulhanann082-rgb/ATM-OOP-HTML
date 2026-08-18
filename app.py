"""
ATM System - Flask application entry point.

This file ONLY wires up routes. All business logic lives in services/
and models/ - routes just: read input, call a service, catch ATM
exceptions, and render a template. No raw stack traces are ever shown
to the user (see the 500 handler and the try/except blocks below).
"""

from __future__ import annotations

from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_wtf import CSRFProtect

from config import Config
from database.db import db
from models import Customer, Account
from models.bank import Bank
from services.auth_service import AuthService
from services.account_service import AccountService
from exceptions.custom_exceptions import ATMException

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
csrf = CSRFProtect(app)


# ---------------------------------------------------------------------- #
# Helpers / decorators
# ---------------------------------------------------------------------- #
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "customer_db_id" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def account_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "account_id" not in session:
            flash("Please select an account first.", "error")
            return redirect(url_for("select_account"))
        return view(*args, **kwargs)
    return wrapped


def current_customer() -> Customer | None:
    customer_db_id = session.get("customer_db_id")
    return Customer.query.get(customer_db_id) if customer_db_id else None


def current_account() -> Account | None:
    account_id = session.get("account_id")
    if not account_id:
        return None
    account = Account.query.get(account_id)
    customer = current_customer()
    if account and customer:
        Bank.ensure_owned_by(account, customer)  # authorization guard on every access
    return account


# ---------------------------------------------------------------------- #
# Auth routes
# ---------------------------------------------------------------------- #
@app.route("/", methods=["GET"])
def index():
    if "customer_db_id" in session:
        return redirect(url_for("select_account"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    card_number = request.form.get("card_number", "").strip()
    pin = request.form.get("pin", "").strip()

    if not card_number or not pin:
        flash("Card number and PIN are required.", "error")
        return render_template("login.html")

    try:
        customer = AuthService.login(card_number, pin)
    except ATMException as e:
        flash(e.message, "error")
        return render_template("login.html")

    session.clear()
    session["customer_db_id"] = customer.id
    session["customer_name"] = customer.name
    flash(f"Welcome, {customer.name}!", "success")
    return redirect(url_for("select_account"))


@app.route("/select-account", methods=["GET", "POST"])
@login_required
def select_account():
    customer = current_customer()
    accounts = AuthService.get_customer_accounts(customer)

    if request.method == "GET":
        if len(accounts) == 1:
            session["account_id"] = accounts[0].id
            return redirect(url_for("dashboard"))
        return render_template("select_account.html", accounts=accounts)

    account_number = request.form.get("account_number")
    try:
        account = AuthService.select_account(customer, account_number)
    except ATMException as e:
        flash(e.message, "error")
        return render_template("select_account.html", accounts=accounts)

    session["account_id"] = account.id
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out securely.", "success")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------- #
# Dashboard
# ---------------------------------------------------------------------- #
@app.route("/dashboard")
@login_required
@account_required
def dashboard():
    account = current_account()
    return render_template("dashboard.html", account=account)


# ---------------------------------------------------------------------- #
# Balance
# ---------------------------------------------------------------------- #
@app.route("/balance")
@login_required
@account_required
def balance():
    account = current_account()
    try:
        bal = AccountService.check_balance(account)
    except ATMException as e:
        flash(e.message, "error")
        return redirect(url_for("dashboard"))
    return render_template("balance.html", account=account, balance=bal)


# ---------------------------------------------------------------------- #
# Deposit
# ---------------------------------------------------------------------- #
@app.route("/deposit", methods=["GET", "POST"])
@login_required
@account_required
def deposit():
    account = current_account()
    if request.method == "GET":
        return render_template("deposit.html", account=account)

    try:
        amount = float(request.form.get("amount", 0))
        txn = AccountService.deposit(account, amount)
        flash(
            f"Deposit successful. Transaction ID: {txn.transaction_id}. "
            f"New Balance: Rs. {account.balance:,.2f}",
            "success",
        )
        return redirect(url_for("dashboard"))
    except ValueError:
        flash("Please enter a valid numeric amount.", "error")
    except ATMException as e:
        flash(e.message, "error")

    return render_template("deposit.html", account=account)


# ---------------------------------------------------------------------- #
# Withdraw
# ---------------------------------------------------------------------- #
@app.route("/withdraw", methods=["GET", "POST"])
@login_required
@account_required
def withdraw():
    account = current_account()
    if request.method == "GET":
        return render_template("withdraw.html", account=account)

    try:
        amount = float(request.form.get("amount", 0))
        txn, note_plan = AccountService.withdraw(account, amount)
        notes_str = ", ".join(f"{count} x Rs.{note}" for note, count in sorted(note_plan.items(), reverse=True))
        flash(
            f"Withdrawal successful. Transaction ID: {txn.transaction_id}. "
            f"Dispensed: {notes_str}. New Balance: Rs. {account.balance:,.2f}",
            "success",
        )
        return redirect(url_for("dashboard"))
    except ValueError:
        flash("Please enter a valid numeric amount.", "error")
    except ATMException as e:
        flash(e.message, "error")

    return render_template("withdraw.html", account=account)


# ---------------------------------------------------------------------- #
# Transfer
# ---------------------------------------------------------------------- #
@app.route("/transfer", methods=["GET", "POST"])
@login_required
@account_required
def transfer():
    account = current_account()
    if request.method == "GET":
        return render_template("transfer.html", account=account)

    try:
        receiver_account_number = request.form.get("receiver_account", "").strip()
        amount = float(request.form.get("amount", 0))
        sender_txn, _ = AccountService.transfer(account, receiver_account_number, amount)
        flash(
            f"Transfer successful. Transaction ID: {sender_txn.transaction_id}. "
            f"New Balance: Rs. {account.balance:,.2f}",
            "success",
        )
        return redirect(url_for("dashboard"))
    except ValueError:
        flash("Please enter a valid numeric amount.", "error")
    except ATMException as e:
        flash(e.message, "error")

    return render_template("transfer.html", account=account)


# ---------------------------------------------------------------------- #
# Change PIN
# ---------------------------------------------------------------------- #
@app.route("/change-pin", methods=["GET", "POST"])
@login_required
@account_required
def change_pin():
    account = current_account()
    if request.method == "GET":
        return render_template("change_pin.html", account=account)

    current = request.form.get("current_pin", "")
    new = request.form.get("new_pin", "")
    confirm = request.form.get("confirm_pin", "")

    try:
        card = Bank.find_card_for_customer(current_customer())
        AccountService.change_pin(account, card, current, new, confirm)
        flash("PIN changed successfully.", "success")
        return redirect(url_for("dashboard"))
    except ATMException as e:
        flash(e.message, "error")

    return render_template("change_pin.html", account=account)


# ---------------------------------------------------------------------- #
# Mini statement
# ---------------------------------------------------------------------- #
@app.route("/mini-statement")
@login_required
@account_required
def mini_statement():
    account = current_account()
    try:
        transactions = AccountService.mini_statement(account, limit=5)
    except ATMException as e:
        flash(e.message, "error")
        return redirect(url_for("dashboard"))
    return render_template("mini_statement.html", account=account, transactions=transactions)


# ---------------------------------------------------------------------- #
# Error handlers - never leak stack traces
# ---------------------------------------------------------------------- #
@app.errorhandler(404)
def not_found(_e):
    return render_template("error.html", message="Page not found."), 404


@app.errorhandler(500)
def server_error(_e):
    return render_template("error.html", message="Something went wrong. Please try again."), 500


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
