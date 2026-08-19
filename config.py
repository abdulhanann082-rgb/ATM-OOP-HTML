"""Application configuration."""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # In a real deployment this MUST come from an environment variable.
    SECRET_KEY = os.environ.get("ATM_SECRET_KEY", "dev-secret-key-change-me")

    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "atm_system.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session / CSRF cookie hardening
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_ENABLED = True
