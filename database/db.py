"""
Central SQLAlchemy database handle.

A single `db` object is created here and imported everywhere else
(models, services, app.py) so there is exactly one SQLAlchemy instance
for the whole application.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
