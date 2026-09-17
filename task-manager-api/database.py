"""Instância do ORM e ciclo de vida do banco.

`db` continua sendo importável como antes (`from database import db`); a criação do schema
passou a acontecer em `init_app`, chamado pela app factory, e não mais em tempo de import.
"""
import sqlite3

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
    """SQLite só impõe FOREIGN KEY com o PRAGMA ligado em cada conexão."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def init_app(app):
    db.init_app(app)
    with app.app_context():
        import models  # noqa: F401  — registra as tabelas antes do create_all

        db.create_all()
