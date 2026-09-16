"""Ciclo de vida da conexão SQLite: uma conexão por request (flask.g) e helper de transação."""
import sqlite3
from contextlib import contextmanager

from flask import current_app, g

from config import settings
from database import schema, seed


def _connect(db_path, readonly=False):
    if readonly:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    else:
        conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db():
    if "db" not in g:
        g.db = _connect(current_app.config["DB_PATH"])
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


@contextmanager
def transaction():
    """Commit ao sair sem erro, rollback em exceção. Reentrante: blocos aninhados participam
    da transação externa (só o bloco mais externo faz commit/rollback)."""
    conn = get_db()
    depth = g.get("_tx_depth", 0)
    g._tx_depth = depth + 1
    try:
        yield conn
        if depth == 0:
            conn.commit()
    except Exception:
        if depth == 0:
            conn.rollback()
        raise
    finally:
        g._tx_depth = depth


@contextmanager
def readonly_connection():
    """Conexão somente leitura (mode=ro) para consultas administrativas ad hoc."""
    conn = _connect(current_app.config["DB_PATH"], readonly=True)
    try:
        yield conn
    finally:
        conn.close()


def init_app(app):
    app.config.setdefault("DB_PATH", settings.DB_PATH)
    app.teardown_appcontext(close_db)
    conn = _connect(app.config["DB_PATH"])
    try:
        schema.create_tables(conn)
        seed.run_if_empty(conn)
    finally:
        conn.close()
